#!/usr/bin/env python3
"""Render isolated failure examples; never apply them to a cluster."""
import argparse
from pathlib import Path

from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[2]
HOST = 'app-test.ns.svc.cluster.local'
TROUBLE = 'playground-trouble.prod-playground-trouble.svc.cluster.local'


def resource(kind, name, spec, api='networking.istio.io/v1'):
    return dict(apiVersion=api, kind=kind, metadata=dict(name=name), spec=spec)


def dr(host=HOST, **policy):
    return resource('DestinationRule', 'fault-lab', dict(host=host, exportTo=['.'], trafficPolicy=policy))


def vs(host=HOST, gateway='mesh', subset=None, **route_settings):
    dest=dict(host=host, port=dict(number=80))
    if subset: dest['subset']=subset
    route=dict(route=[dict(destination=dest)], **route_settings)
    return resource('VirtualService', 'fault-lab', dict(hosts=['wp.pl'] if gateway!='mesh' else [host],
                    gateways=[gateway], exportTo=['.'], http=[route]))


def service(name, selector):
    return resource('Service', name, dict(selector=selector, ports=[dict(name='http', port=80, targetPort=8080)]), 'v1')


def deployment(name, container, readiness=None):
    if readiness: container['readinessProbe']=readiness
    container['securityContext']=dict(allowPrivilegeEscalation=False,readOnlyRootFilesystem=True,capabilities=dict(drop=['ALL']))
    return resource('Deployment', name, dict(replicas=1, selector=dict(matchLabels=dict(app=name)),
        template=dict(metadata=dict(labels={'app':name,'sidecar.istio.io/inject':'true'}),
                      spec=dict(securityContext=dict(runAsNonRoot=True,runAsUser=1000,seccompProfile=dict(type='RuntimeDefault')),
                                containers=[container]))), 'apps/v1')


def bad_cluster(context):
    return resource('EnvoyFilter','bad-connect-timeout',dict(configPatches=[dict(
        applyTo='CLUSTER', match=dict(context=context, cluster=dict(service=HOST, portNumber=80)),
        patch=dict(operation='MERGE', value=dict(connect_timeout='-1s')))])) | {'apiVersion':'networking.istio.io/v1alpha3'}


def limited_pool(host=HOST):
    return dr(host, connectionPool=dict(tcp=dict(maxConnections=1),
        http=dict(http1MaxPendingRequests=1,http2MaxRequests=1,h2UpgradePolicy='DO_NOT_UPGRADE')))


def patch(name, containers=None, annotations=None):
    template={}
    if containers: template['spec']=dict(containers=containers)
    if annotations: template['metadata']=dict(annotations=annotations)
    return resource('Deployment',name,dict(template=template),'apps/v1')


def case(title, metrics, effect, documents=(), label=None):
    parts=['## '+title, ' · '.join('`'+m+'`' for m in metrics), effect]
    if label: parts.append('**'+label+'**')
    if documents: parts.append('```yaml\n'+dump_documents(documents).strip()+'\n```')
    return '\n\n'.join(parts)


def pages():
    x=[]
    deny_xds=resource('NetworkPolicy','block-xds',dict(podSelector=dict(matchLabels=dict(app='app-test')),
        policyTypes=['Egress'],egress=[dict(ports=[dict(protocol='UDP',port=53),dict(protocol='TCP',port=53),
        dict(protocol='TCP',port=80),dict(protocol='TCP',port=443),dict(protocol='TCP',port=8080)])]),'networking.k8s.io/v1')
    x.append(case('Disconnected proxies',['pilot_xds'],
        'Client namespace; NetworkPolicy enforcement required, with no other policy allowing port 15012. On reconnect, app-test cannot reach Istiod; existing connections may survive until closed.',[deny_xds]))
    x.append(case('Slow configuration delivery',['pilot_proxy_convergence_time_bucket','pilot_proxy_queue_time_bucket','pilot_xds_push_time_bucket'],
        'Low Istiod CPU limits can grow queues and convergence time under load. Change lab configuration while generating traffic; idle Istiod may show no slowdown.',
        [dict(resources=dict(requests=dict(cpu='10m'),limits=dict(cpu='10m')))],'Istiod chart values · isolated control plane'))
    x.append(case('Endpoint churn',['pilot_k8s_reg_events','pilot_push_triggers'],
        'Readiness flips every five seconds → endpoint updates and repeated pushes. This creates configuration churn without restarting the application.',[
        deployment('churn-lab',dict(name='app',image='busybox:1.37.0',command=['httpd','-f','-p','8080']),
            dict(exec={'command':['sh','-c','test $(( $(date +%s) / 5 % 2 )) -eq 0']},periodSeconds=1,successThreshold=1,failureThreshold=1)),
        service('churn-lab',dict(app='churn-lab'))]))
    conflicts=[]
    for name,ip in [('one','192.0.2.10'),('two','192.0.2.20')]:
        conflicts.append(resource('ServiceEntry',name,dict(hosts=[name+'.wp.pl'],addresses=['198.51.100.10'],
            exportTo=['.'],location='MESH_EXTERNAL',resolution='STATIC',
            ports=[dict(number=9000,name='tcp',protocol='TCP')],endpoints=[dict(address=ip)])))
    x.append(case('Conflicting TCP listeners',['pilot_conflict_outbound_listener_tcp_over_current_tcp'],
        'Two TCP services claim the same VIP:9000. Inspect the conflict counter and generated listener; both destinations cannot be distinguished on that address.',conflicts))
    x.append(case('Service without endpoints',['pilot_eds_no_instances'],
        'No Pod has app=does-not-exist. The service has no endpoints; inspect EDS and the selector.',[service('empty-lab',dict(app='does-not-exist'))]))
    x.append(case('Pods never become ready',['pilot_endpoint_not_ready','pilot_eds_no_instances'],
        'The process runs but its readiness probe always fails. EndpointSlices contain an unready endpoint; it is excluded from normal routing.',[
        deployment('unready-lab',dict(name='app',image='busybox:1.37.0',command=['httpd','-f','-p','8080']),
            dict(exec={'command':['sh','-c','exit 1']},periodSeconds=2,failureThreshold=1)),service('unready-lab',dict(app='unready-lab'))]))
    x.append(case('Envoy rejects a cluster',['envoy_cluster_manager_cds_update_rejected'],
        'Client namespace; app-test.ns must exist. The negative connect timeout is deliberately invalid for Envoy. Expect a CDS NACK; inspect the proxy counter in Gateway/Workload and Istiod logs.',[bad_cluster('SIDECAR_OUTBOUND')]))
    gateway=resource('Gateway','gateway-blue',dict(selector=dict(istio='gateway-blue'),servers=[dict(
        port=dict(number=443,name='https',protocol='HTTPS'),hosts=['wp.pl'],tls=dict(mode='SIMPLE',credentialName='missing-lab-cert'))]))
    x.append(case('Gateway waits for an absent TLS Secret',['envoy_listener_manager_total_listeners_warming'],
        'Use the gateway namespace. missing-lab-cert must not exist; replace the lab listener/route. A new HTTPS listener waits for SDS. An existing listener may keep its previous certificate.',[gateway,vs(gateway='gateway-blue')]))
    x.append(case('Sidecar excludes a dependency',[],
        'Client namespace; replace its existing Sidecar. app-test.ns is excluded. With REGISTRY_ONLY, requests to it are blocked; xDS may remain fully synced.',[
        resource('Sidecar','default',dict(egress=[dict(hosts=['istio-system/*'])],outboundTrafficPolicy=dict(mode='REGISTRY_ONLY')))]))
    remote_config=dict(apiVersion='v1',kind='Config',clusters=[dict(name='remote-lab',cluster=dict(server='https://127.0.0.1:1'))],
        users=[dict(name='remote-lab',user=dict(token='invalid-lab-token'))],
        contexts=[dict(name='remote-lab',context=dict(cluster='remote-lab',user='remote-lab'))],**{'current-context':'remote-lab'})
    secret=dict(apiVersion='v1',kind='Secret',metadata=dict(name='istio-remote-secret-remote-lab',
        labels={'istio/multiCluster':'true'},annotations={'networking.istio.io/cluster':'remote-lab'}),
        type='Opaque',stringData={'remote-lab':dump_documents([remote_config])})
    x.append(case('Remote cluster cannot be synchronized',['istiod_managed_clusters'],
        'Isolated istio-system namespace. The remote API address refuses connections. Check remote-clusters and Istiod logs; managed-cluster count alone does not prove connectivity.',[secret]))

    g=[]
    missing=resource('DestinationRule','fault-lab',dict(host=HOST,exportTo=['.'],subsets=[dict(name='missing',labels=dict(version='does-not-exist'))]))
    g.append(case('No healthy upstream',['envoy_cluster_upstream_cx_none_healthy'],
        'Replace the lab gateway route; no backend Pod matches the subset. Requests for wp.pl produce UH/503 even though other subsets may be healthy.',[missing,vs(gateway='gateway-blue',subset='missing')]))
    g.append(case('TLS sent to a plaintext backend',['envoy_cluster_upstream_cx_connect_fail','envoy_cluster_upstream_cx_connect_timeout'],
        'Gateway namespace; the existing route targets app-test.ns:80, which serves plaintext HTTP. SIMPLE forces TLS to that port. Send requests and inspect UF and transport failure reasons.',[dr(tls=dict(mode='SIMPLE',sni='wp.pl'))]))
    g.append(case('Connection pool overflow',['envoy_cluster_upstream_rq_pending_overflow'],
        'Gateway namespace; backend app-test.ns:80 must take about 3 seconds. Send at least 20 concurrent requests through the gateway → UO/overflow. Sequential requests may succeed.',[limited_pool()]))
    g.append(case('Rejected configuration',['envoy_cluster_manager_cds_update_rejected'],
        'Gateway namespace; app-test.ns:80 must already be routed. This deliberately invalid Envoy timeout triggers CDS rejection; the previous valid configuration may remain active.',[bad_cluster('GATEWAY')]))
    g.append(case('Gateway CPU or memory pressure',['container_cpu_usage_seconds_total','container_memory_working_set_bytes','kube_pod_container_status_restarts_total'],
        'Apply as a strategic merge patch to the lab gateway. Under load, very small limits can cause throttling or OOM/restarts. Confirm termination reasons; CPU usage alone is not proof.',[
        patch('gateway-blue',[dict(name='istio-proxy',resources=dict(requests=dict(cpu='10m',memory='16Mi'),limits=dict(cpu='10m',memory='16Mi')))])],
        'Deployment patch · existing gateway-blue'))

    w=[]
    w.append(case('Retries hide failures',['envoy_cluster_upstream_rq_retry','envoy_cluster_upstream_rq_retry_limit_exceeded'],
        'Replace the lab route. Trouble /test/cosmos-retry must return a mix of 200/503. Repeated requests produce retries and sometimes a final 200; an always-200 backend will not reproduce this.',[
        vs(TROUBLE,retries=dict(attempts=2,perTryTimeout='1s',retryOn='5xx'),timeout='5s')]))
    w.append(case('Response deadline is too short',['envoy_cluster_upstream_rq_timeout'],
        'Replace the lab route. Trouble /test/cosmos-timeout takes 3 seconds; the client proxy stops waiting after 100 ms. Send a request → response timeout, commonly 504.',[
        vs(TROUBLE,retries=dict(attempts=0),timeout='100ms')]))
    w.append(case('Circuit breaker rejects concurrent requests',['envoy_cluster_upstream_rq_pending_overflow'],
        'Client namespace. Trouble /test/cosmos-connections takes 3 seconds. Use this route and send at least 20 concurrent requests; the small pool rejects excess requests.',[
        limited_pool(TROUBLE),vs(TROUBLE,retries=dict(attempts=0),timeout='10s')]))
    reset_script='''import socket, socketserver, struct
class Reset(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.recv(4096)
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        self.request.close()
socketserver.TCPServer.allow_reuse_address = True
socketserver.TCPServer(("0.0.0.0", 8080), Reset).serve_forever()
'''
    w.append(case('Application resets upstream requests',['envoy_cluster_upstream_rq_rx_reset'],
        'Send HTTP requests to reset-lab:80. The application resets its TCP socket. Inspect the destination sidecar inbound cluster and reset logs; the client sidecar may only see the resulting 503.',[
        deployment('reset-lab',dict(name='app',image='python:3.12-alpine',command=['python','-u','-c'],args=[reset_script])),
        service('reset-lab',dict(app='reset-lab'))]))
    w.append(case('Application or Envoy overload',['container_cpu_usage_seconds_total','container_memory_working_set_bytes','kube_pod_container_status_restarts_total','kube_pod_init_container_status_restarts_total'],
        'Strategic merge patch for an existing app-test Deployment with container api. Small application limits isolate application pressure; proxy limits remain unchanged. Check api OOM/throttling separately from istio-proxy.',[
        patch('app-test',[dict(name='api',resources=dict(requests=dict(cpu='10m',memory='8Mi'),limits=dict(cpu='10m',memory='8Mi')))])],
        'Deployment patch · existing api container'))
    return {'XDS.md':x,'GATEWAY.md':g,'WORKLOAD.md':w}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    for name,sections in pages().items():
        path=ROOT/'docs/observability'/name
        content='\n\n'.join(sections)+'\n'
        if args.check: assert path.read_text()==content,path
        else: path.write_text(content)
    print('Observability examples match their source.' if args.check else 'Observability examples rendered.')


if __name__=='__main__':
    main()
