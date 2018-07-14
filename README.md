# Envoy for Google Cloud Identity Aware Proxy


Sample [Envoy Proxy](https://www.envoyproxy.io/) config to validate JWT authentication headers used by GCP [Identity Aware Proxy](https://cloud.google.com/iap/docs/).

When you use IAP, Google will handle the application-level access control model for you by default by making sure only those users or groups are allowed through.

However, its advisable to always validate those headers in your applicaiton as well as a secondary check:
- [https://cloud.google.com/iap/docs/signed-headers-howto](https://cloud.google.com/iap/docs/signed-headers-howto)

You can always validate the headers in your application code using middleware as shown in ```http_server.py```.  However, its not always possible to modify your applicaiton code to do this and its desireable to inject anotother proxy infront of your application that handles this for you.  This is similar to how [istio](https://istio.io/) and [Google Cloud Endpoints ESP](https://cloud.google.com/endpoints/docs/openapi/get-started-compute-engine-docker#running_the_api_and_extensible_service_proxy_in_a_docker_container) works.  

In this example, we're going to spin up a simple Envoy proxy that just does the JWT validaiton for you and then passes that header as-is or transformed to your app anyway so you can identity the actual user.

That is

```user --> IAP --> envoy --> your_app```

The JWT header sent by IAP is re validated for you by envoy


## Configure IAP 

This technique mostly applies to an application running in Google Kubernetes Engine or Compute Engine where you are free to run a docker container or envoy stand-alone.

Once you've configured IAP in either of these enviornments,

-  [IAP for Compute Engine](https://cloud.google.com/iap/docs/enabling-compute-howto)
-  [IAP for Kubernetes Engine](https://cloud.google.com/iap/docs/enabling-kubernetes-howto)

Note down the ```Audience``` the  ```X-Goog-Iap-Jwt-Assertion``` will use in [Verify IAP Payload](https://cloud.google.com/iap/docs/signed-headers-howto#verify_the_jwt_payload)

We will use that to setup Envoy

## Configure Envoy

The envoy config uses the ```jwt_authn``` http filter capability (see [jwt_authn](https://github.com/envoyproxy/data-plane-api/blob/master/envoy/config/filter/http/jwt_authn/v2alpha/README.md
))

Which in the envoy config format, looks like:

```yaml
          http_filters:
          - name: envoy.filters.http.jwt_authn
            config:
              providers:
                google-jwt:
                  issuer: https://cloud.google.com/iap
                  audiences:
                  - /projects/1071284184436/apps/mineral-minutia-820
                  forward: true
                  remote_jwks:
                    http_uri:
                      uri: https://www.gstatic.com/iap/verify/public_key-jwk
                      cluster: jwt.www.googleapis.com|443
                  from_headers:
                  - name: X-Goog-Iap-Jwt-Assertion
              rules:
              - match:
                  prefix: "/todos"
                requires:
                  provider_name: "google-jwt"
          - name: envoy.router
            config: {}
```

Envoy will process a JWT in the format below and look for it in the ```X-Goog-Iap-Jwt-Assertion``` header

```json
{
  "alg": "ES256",
  "typ": "JWT",
  "kid": "5PuDqQ"
}
.
{
  "iss": "https://cloud.google.com/iap",
  "sub": "accounts.yourcompany.com:1081579130932224845548",
  "email": "srashid@yourcompany.com",
  "aud": "/projects/1071284184436/apps/mineral-minutia-820",
  "exp": 1531490127,
  "iat": 1531489527,
  "hd": "yourcompany.com"
}
```

Note the audience i've used there and the full config sample ```envoy_iap.yaml```

The following link shows the JWK endpoint to use for the EC public keys:
 - [https://www.gstatic.com/iap/verify/public_key-jwk](https://www.gstatic.com/iap/verify/public_key-jwk)

If you want to run envoy standaline, start your backend/upstream service and run start envoy:

```
envoy -c envoy_iap.yaml -l debug
```

If you would rather run this in a docker container (recommended), generate the image in anyway you'd like using envoy's dockerhub:

```dockerfile
FROM envoyproxy/envoy:latest
COPY envoy_iap.yaml /etc/envoy/envoy.yaml
```

then if your upstreamservice is local, you need to point 

```
docker build -t envoy:v1 .
docker run -p 10000:10000 --net host -t envoy:v1
```


## Appendix

### Sample Client/Server

In this repo, you'll also find a smaple client/server app in python.

to use, first

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

then
```
python http_server.py
```

If you want to test locally with ```http_client.py```, first get an IAP token that is sent to your app that is currently on GCP (eg, by logging it to cloud logging).
Then start envoy and the backend ```http_server.py```.  Copy the JWT into the code and invoke it.  This is only for testing your envoy and backend config.


### Envoy Control and Dataplane helloworld

You dont' have to staticlly cofigure envoy proxy.  One of its many capabilities is to allow remote config.  
For more information, see

- [https://github.com/salrashid123/envoy_control](https://github.com/salrashid123/envoy_control)
- [https://github.com/salrashid123/envoy_discovery](https://github.com/salrashid123/envoy_discovery)


### Envoy for google_id_token validation

As an extra, this repo also contains a sample for validating a ```google_id_token``` as issued by gcloud cli.
This is really just a test but if you want to try it out, run envoy with ```envoy_google.yaml``` and then note the sections
commented out in ```http_client.py```.