# Version control


Mathias DURAT -  Dorian GRASSET - Isalyne LLINARES—RAMES

---

# Objectifs

- Installer ArgoCD via Helm
- Installer Postgresql en haute disponibilité
- Installer Airflow via ArgoCD
- Proposer une pipeline de déploiement pour Airflow + Dags + Postgresql

# Prérequis

- **Cluster Kubernetes** opérationnel.
- **kubectl** configuré et connecté au cluster.
- **Helm** installé et configuré pour le cluster Kubernetes.
- **ArgoCD CLI** installé.
- **K9s** (facultatif) pour une gestion plus conviviale du cluster.
- Accès aux dépôts de charts Helm, comme ceux de **ArgoCD** et **Bitnami**.

# Installer ArgoCD via Helm

Créer un namespace et [installer ArgoCD](https://artifacthub.io/packages/helm/argo/argo-cd) sur le cluster :

```bash
kubectl create ns argocd
helm repo add argo https://argoproj.github.io/argo-helm
helm --version 7.6.8 -n argocd install my-argo-cd argo/argo-cd
```

Faire un port forward du service `argocd-server` sur 8080:8080.

Accéder à l'interface ArgoCD via [https://localhost:8080](https://localhost:8080/).

Pour récupérer le mot de passe admin par défaut :

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Connectez-vous à l'interface avec le login **admin** et le mot de passe récupéré.

# Installer une Postgresql HA via ArgoCD

Créer un namespace pour Airflow de la manière suivante :

```bash
kubectl create ns airflow
```

Ajouter le [repository helm de **Bitnami**](https://charts.bitnami.com/) et installer PostgreSQL en haute disponibilité :

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

Créer un fichier `postgresql-ha.yaml` pour ArgoCD :

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: postgresql
spec:
  destination:
    name: ''
    namespace: airflow
    server: https://kubernetes.default.svc
  source:
    path: ''
    repoURL: https://charts.bitnami.com/bitnami
    targetRevision: 14.2.33
    chart: postgresql-ha
    helm:
      values: |
        global:
          postgresql:
            username: "postgres"
            password: "postgrespassword"
            database: "my_database"
            repmgrUsername: "repmgr"
            repmgrPassword: "replpassword"
            repmgrDatabase: "my_database"
          pgpool:
            adminUsername: "postgres"
            adminPassword: "postgrespassword"
  project: default
  syncPolicy:
    automated: null
    syncOptions:
      - CreateNamespace=true
```

Appliquer ce fichier pour déployer PostgreSQL HA via ArgoCD :

```jsx
kubectl apply -f postgresql-ha.yaml -n argocd
```

Se connecter à ArgoCD via le CLI (avec les mêmes identifiants que précedemment) :

```jsx
argocd login localhost:8080
```


Synchroniser l’application PostgreSQL :

```jsx
argocd app sync postgresql
```

# Installer Airflow via ArgoCD

Créer un clef ssh grâce a la commande :

```sql
ssh-keygen
```

Ajouter la clef ssh au repository github:

- Aller dans GitHub repository → Settings → Deploy keys → Add Deploy Key.
- Cocher "Allow write access" .

Créer un secret contenant la clef ssh qui sera utilisé plus tard par Airflow :

```bash
kubectl create secret generic airflow-ssh-key --from-file=gitSshKey=</path/to/ssh/key> -n airflow
secret/airflow-ssh-key created
```

Créer un fichier `airflow.yaml` pour ArgoCD :

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: airflow
  namespace: argocd
spec:
  project: default
  source:
    path: ''
    repoURL: 'https://airflow.apache.org'
    chart: airflow
    targetRevision: 1.15.0
    helm:
      values: |
        createUserJob:
          useHelmHooks: false #Disable this if you are using ArgoCD
        migrateDatabaseJob:
          useHelmHooks: false #Disable this if you are using ArgoCD
        data:
          metadataConnection:
            user: postgres
            pass: postgrespassword
            protocol: postgresql
            host: postgresql-postgresql-ha-pgpool
            port: 5432
            db: my_database
            sslmode: disable
        postgresql:
          enabled: false
        dags:
          gitSync:
            branch: main
            ref: main
            enabled: true
            repo: git@github.com:DO-2K23-26/source-control-idm.git
            sshKeySecret: airflow-ssh-key
            knownHosts: |
              github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
              github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=
              github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=

  destination:
    server: 'https://kubernetes.default.svc'
    namespace: airflow
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Appliquer ce fichier pour déployer Airflow :

```bash
kubectl apply -f airflow.yaml -n argocd 
```

Synchroniser l'application Airflow via ArgoCD: 

```bash
argocd app sync airflow
```

Vérifier que airflow fonctionne bien en faisant un port forward du service airflow-webserver

```bash
kubectl -n airflow port-forward svc/airflow-webserver 8080:8080
```

On peut maintenant se connecter dessus a adresse http://localhost:8080 avec les credentials :

```
username: admin
password: admin
```

# Pipeline de déploiement pour Airflow + Dags

Maintenant il n’y a plus qu’a créer une pipeline dans notre repository dans le répertoire /tests/dags