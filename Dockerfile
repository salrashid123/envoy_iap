FROM envoyproxy/envoy:latest
COPY envoy_iap.yaml /etc/envoy/envoy.yaml
#COPY envoy_google.yaml /etc/envoy/envoy.yaml