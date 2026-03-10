kubectl apply -k kustomize/overlays/dev
kubectl apply -k kustomize/overlays/prod
kubectl get pods -n careertrojan
kubectl rollout status deploy/backend-api -n careertrojan
kubectl logs -n careertrojan deploy/backend-api --tail=200 -f
kubectl logs -n careertrojan deploy/worker-zendesk-ai --tail=200 -f
kubectl port-forward -n careertrojan svc/backend-api 8600:80
kubectl port-forward -n careertrojan svc/web 8080:80

