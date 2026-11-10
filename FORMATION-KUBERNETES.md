# Formation Kubernetes — du conteneur au cluster
Support complet · 8 modules, 24 leçons, 96 étapes, 64 QCM, 10 labs.
Généré le 10/11/2026.


---

# Module 1 — Du conteneur au cluster

## Pourquoi Kubernetes

### Le conteneur seul ne suffit pas

Une image Docker lancée à la main ne redémarre pas toute seule, ne se répartit pas sur plusieurs machines et ne survit pas à la panne d'un serveur. Kubernetes ajoute exactement ces trois choses : redémarrage, répartition, résilience.

### Ce que Kubernetes fait

Il maintient un état désiré : vous décrivez ce que vous voulez (trois replicas de cette image), il compare en boucle avec l'état réel et corrige l'écart. C'est le principe de réconciliation, et c'est le cœur du système.

### Ce que Kubernetes ne fait pas

Il ne construit pas vos images, ne gère pas vos secrets d'entreprise, ne remplace ni un CDN ni une base de données. Il orchestre des conteneurs, rien de plus. Beaucoup de projets souffrent d'avoir attendu autre chose.

### Quand ne pas l'utiliser

Un site statique, un cron et une petite API ne justifient pas un cluster. Trois conteneurs sur une machine avec docker compose coûtent moins cher en temps, en argent et en compétences. Kubernetes se justifie à partir du moment où il y a plusieurs équipes, plusieurs environnements ou une exigence de disponibilité réelle.

## L'architecture en une page

### Le control plane

Quatre briques : l'API server, etcd, le scheduler et le controller-manager. L'API server est la porte d'entrée : tout passe par lui, en HTTPS. etcd stocke l'état complet du cluster. Le scheduler choisit le nœud. Le controller-manager exécute les boucles de réconciliation.

### Les nœuds

Sur chaque machine de travail tournent le kubelet (qui parle à l'API server et pilote les conteneurs), le runtime de conteneurs (containerd le plus souvent) et kube-proxy (qui programme les règles réseau). Un nœud n'est rien d'autre qu'une machine avec ces trois composants.

### Le trajet d'une commande

kubectl envoie une requête HTTPS à l'API server. Celui-ci authentifie, autorise (RBAC), valide (admission), puis écrit l'objet dans etcd. Le controller-manager voit la nouveauté, crée ce qui manque. Le scheduler assigne le pod. Le kubelet du nœud choisi crée le conteneur.

### Ce qui tombe si etcd tombe

Tout. Le cluster perd la mémoire : l'API server ne peut plus lire ni écrire, les contrôleurs s'arrêtent, les applications continuent de tourner un moment puis s'arrêtent faute de pouvoir signaler leur état. La sauvegarde d'etcd n'est pas une option avancée, c'est la base.

## Installer un cluster local

### Minikube

Un nœud unique dans une machine virtuelle ou un conteneur. Commande : minikube start. C'est le plus simple pour apprendre, et suffisant pour 90 pour cent des exercices de cette formation.

### Kind

Kind crée des clusters multi-nœuds dans des conteneurs Docker, en quelques secondes. Commande : kind create cluster --name demo. C'est le meilleur outil pour tester une topologie réaliste, un DaemonSet ou un problème réseau.

### Vérifier que ça tourne

kubectl get nodes doit montrer un nœud Ready. kubectl get pods -A montre les composants système. Si un pod système est en CrashLoopBackOff dès l'installation, le problème est presque toujours la mémoire de la VM ou le runtime.

### Gérer les contextes

kubectl config get-contexts liste les clusters connus, kubectl config use-context bascule de l'un à l'autre. Sur une machine qui a plusieurs clusters, la première cause d'erreur est de taper des commandes dans le mauvais contexte. Vérifiez toujours avant une opération destructrice.


---

# Module 2 — Les objets de base

## Le Pod

### La plus petite unité

Un pod contient un ou plusieurs conteneurs qui partagent le réseau et les volumes. Deux conteneurs dans un pod se parlent par localhost et partagent la même adresse IP. C'est le pattern sidecar : un conteneur applicatif, un conteneur auxiliaire.

### Le cycle de vie

Un pod naît, tourne, meurt. Il n'est pas réparé : si le nœud tombe, un pod nu disparaît avec lui. C'est pour cela qu'on ne crée presque jamais de pod directement en production, mais un Deployment qui en fabrique.

### restartPolicy

Always par défaut (relance le conteneur), OnFailure (relance seulement en cas d'erreur), Never. Un pod nu avec restartPolicy Always redémarre son conteneur, mais ne survit pas à la perte du nœud. La différence est essentielle.

### Créer et inspecter

kubectl run demo --image=nginx crée un pod. kubectl get pod demo -o yaml montre l'objet complet. kubectl describe pod demo donne l'événementiel, c'est-à-dire pourquoi il ne démarre pas. Le YAML décrit l'intention, describe raconte l'histoire.

## Deployment et ReplicaSet

### Le ReplicaSet

Il garantit un nombre de pods identiques. Vous dites trois, il en maintient trois : il en crée si un meurt, il en supprime si vous baissez le compte. Il utilise un sélecteur de labels pour savoir quels pods sont les siens.

### Le Deployment

Il gère des ReplicaSets successifs et donc les versions. Vous changez l'image, il crée un nouveau ReplicaSet, monte progressivement, et garde l'ancien pour un retour arrière. C'est l'objet standard pour une application sans état.

### Dérouler et vérifier

kubectl create deployment web --image=nginx --replicas=3. kubectl rollout status deployment/web suit la progression. kubectl rollout history deployment/web liste les révisions. kubectl rollout undo deployment/web revient à la précédente.

### Le piège du sélecteur

Un Deployment dont le sélecteur ne correspond à aucun label ne crée rien, sans erreur visible. Vérifiez que spec.selector.matchLabels correspond exactement à spec.template.metadata.labels. C'est l'erreur la plus fréquente chez les débutants.

## Labels, annotations, namespaces

### Labels

Des paires clé/valeur qui servent à sélectionner : kubectl get pods -l app=web. Tout le reste du système repose dessus : services, deployments, network policies. Un label mal orthographié casse une chaîne entière en silence.

### Annotations

Même forme, autre usage : des métadonnées que Kubernetes ne sélectionne pas. Version de build, contact de l'équipe, configuration d'un ingress controller. Ne mettez jamais dans un label ce qui peut être long ou structuré.

### Namespaces

Un cloisonnement logique des noms, pas une frontière de sécurité. Deux équipes dans deux namespaces ne voient pas les mêmes objets par défaut, mais peuvent se joindre en réseau. La sécurité vient du RBAC et des NetworkPolicies, pas du namespace.

### Les commandes utiles

kubectl config set-context --current --namespace=dev évite de taper -n partout. kubectl get all -n dev montre l'essentiel. Attention : 'get all' ne montre pas tout, ni les secrets, ni les configmaps, ni les ingress selon les versions.


---

# Module 3 — Réseau

## Le Service

### À quoi il sert

Un pod a une IP qui change à chaque recréation. Le Service donne une adresse stable et répartit le trafic sur les pods qui portent le bon label. C'est un répartiteur, pas un serveur.

### Les types

ClusterIP : joignable seulement dans le cluster, le défaut. NodePort : ouvre un port sur chaque nœud, utile pour tester. LoadBalancer : demande une IP publique au fournisseur cloud. ExternalName : un alias DNS vers un service externe.

### port et targetPort

port est le port du Service, targetPort le port du conteneur. Les confondre produit un service qui répond mais renvoie des erreurs de connexion. Vérifiez les deux, puis vérifiez les endpoints.

### Vérifier le câblage

kubectl get endpoints mon-service doit lister des adresses. S'il est vide, le sélecteur ne correspond à aucun pod prêt. C'est la première chose à regarder quand un service ne répond pas.

## Ingress

### Un contrôleur est obligatoire

Un objet Ingress ne fait rien tout seul : il faut un ingress controller (NGINX, Traefik, HAProxy) qui lit les objets et configure un vrai proxy. Sur minikube : minikube addons enable ingress.

### Routage par hôte et par chemin

Une règle associe un host et un path à un service. app.exemple.fr vers web:80, /api vers api:8080. L'ordre des règles compte : le chemin le plus précis doit être déclaré avant le générique.

### TLS

Le certificat est stocké dans un Secret de type kubernetes.io/tls, référencé dans spec.tls. Le contrôleur fait la terminaison TLS : le trafic arrive en HTTPS et repart en HTTP vers le pod, sauf configuration contraire.

### Déboguer un 404 ou un 503

404 : aucune règle ne correspond à l'hôte ou au chemin. 503 : la règle existe mais le service n'a pas d'endpoints prêts. Regardez les logs du contrôleur avant de suspecter l'application.

## DNS interne et NetworkPolicy

### Le DNS du cluster

CoreDNS résout les noms de services. Forme complète : mon-service.mon-namespace.svc.cluster.local. Dans le même namespace, le nom court suffit. Hors du namespace, il faut au minimum service.namespace.

### Résoudre pour vérifier

kubectl run tmp --rm -it --image=busybox -- nslookup mon-service. Si le nom ne résout pas, vérifiez que CoreDNS tourne et que le service existe dans le bon namespace. Un nom résolu mais une connexion refusée, c'est autre chose : le port ou les endpoints.

### NetworkPolicy

Par défaut, tout le monde parle à tout le monde. Une NetworkPolicy permet de restreindre par labels, ports et namespaces. Commencez par un deny total dans un namespace de test, puis ouvrez ce qui est nécessaire.

### La limite à connaître

Une NetworkPolicy n'a d'effet que si le plugin réseau l'implémente. Calico, Cilium, Weave le font ; certains plugins minimalistes non. Une politique appliquée sans effet donne un faux sentiment de sécurité.


---

# Module 4 — Configuration et ressources

## ConfigMap et Secret

### Séparer la configuration

Une image doit être la même partout ; ce qui change, ce sont les paramètres. ConfigMap porte les valeurs non sensibles, Secret les valeurs sensibles. Les deux se montent en variables d'environnement ou en fichiers.

### Secret n'est pas un coffre-fort

Par défaut, un Secret est simplement encodé en base64 dans etcd. Activez le chiffrement au repos, ou utilisez un gestionnaire externe (Vault, External Secrets). base64 n'est pas du chiffrement, tout le monde peut le décoder.

### Montage ou variables

En variable d'environnement, la valeur est figée au démarrage du conteneur. En fichier monté, Kubernetes met à jour le contenu, mais l'application doit relire le fichier. Choisissez selon le comportement de votre application.

### Bonnes pratiques

Un ConfigMap par application et par environnement, nommé avec sa version. Évitez de mettre toute la configuration dans un seul objet géant : une modification devient un redéploiement complet.

## Les sondes

### Trois sondes, trois rôles

Liveness : le conteneur est-il vivant ? Sinon, on le tue et on le relance. Readiness : peut-il recevoir du trafic ? Sinon, on le retire des endpoints. Startup : a-t-il fini de démarrer ? Sinon, on attend avant d'appliquer les autres.

### La conséquence concrète

Sans readiness, un pod lent reçoit du trafic avant d'être prêt : erreurs 502 au déploiement. Avec une liveness trop agressive, un pod qui a un pic de charge est tué et relancé en boucle. Les deux erreurs sont symétriques.

### Les types de sonde

httpGet sur un chemin, tcpSocket sur un port, exec d'une commande. Ajoutez initialDelaySeconds, periodSeconds, timeoutSeconds et failureThreshold. Les valeurs par défaut sont rarement adaptées à une application réelle.

### Déboguer une sonde

kubectl describe pod montre les événements Unhealthy. Vérifiez le chemin, le port et le code retour attendu. Une sonde HTTP sur un service qui renvoie 401 ou 302 échoue, même si l'application fonctionne.

## Requests, limits et QoS

### Requests et limits

Requests : ce que le pod demande au scheduler pour être placé. Limits : le plafond qu'il ne peut pas dépasser. Sans requests, le scheduler place au hasard et tout le monde subit.

### Ce qui se passe au dépassement

Limite mémoire dépassée : le conteneur est tué, OOMKilled. Limite CPU dépassée : il est ralenti (throttling), pas tué. Confondre les deux conduit à chercher un crash là où il y a une bride.

### Les classes QoS

Guaranteed : requests égales aux limits partout. Burstable : requests inférieures aux limits. BestEffort : rien de déclaré. En cas de pression mémoire, Kubernetes évince d'abord les BestEffort, puis les Burstable. C'est l'argument décisif pour déclarer des requests.

### Encadrer par namespace

ResourceQuota limite le total d'un namespace, LimitRange impose des valeurs par défaut et des bornes par conteneur. Sans les deux, une équipe peut consommer tout le cluster avec trois manifests mal écrits.


---

# Module 5 — Stockage

## Volumes éphémères

### Pourquoi un volume dans un pod

Deux conteneurs d'un même pod peuvent partager un répertoire. Sans volume, chacun a son système de fichiers, et tout disparaît avec le conteneur. C'est le rôle d'emptyDir.

### emptyDir

Créé au démarrage du pod, détruit avec lui. Parfait pour un cache, des fichiers temporaires, un échange entre sidecars. À ne jamais utiliser pour des données à conserver, même quelques minutes.

### hostPath

Monte un répertoire du nœud dans le pod. Pratique pour un agent de supervision, dangereux pour tout le reste : le pod dépend d'un nœud précis et peut écrire dans le système hôte. À éviter en production.

### Le réflexe

Si la donnée doit survivre au pod, ce n'est pas un volume éphémère qu'il faut, c'est un PersistentVolumeClaim. Se poser la question avant d'écrire le YAML évite une perte de données.

## PV, PVC et StorageClass

### Le modèle déclaratif

Le PersistentVolume est la ressource de stockage réelle. Le PersistentVolumeClaim est la demande : taille, mode d'accès. Kubernetes apparie les deux. L'application ne référence que le PVC.

### Les modes d'accès

ReadWriteOnce : un seul nœud en écriture. ReadOnlyMany : plusieurs nœuds en lecture. ReadWriteMany : plusieurs nœuds en écriture, rare et dépendant du backend. Un PVC en RWO ne peut pas être monté par deux pods sur deux nœuds différents.

### Provisionnement dynamique

Une StorageClass décrit comment créer un volume à la demande. C'est le mode normal dans le cloud : vous créez un PVC, le volume apparaît. Sans StorageClass, il faut créer le PV à la main.

### reclaimPolicy

Delete supprime le volume quand le PVC disparaît. Retain le conserve, à vous de le récupérer. En production, Retain par défaut sur les données précieuses : un kubectl delete malheureux ne doit pas effacer une base.

## StatefulSet

### Ce que le Deployment ne sait pas faire

Un Deployment donne des pods interchangeables, avec des noms aléatoires et des volumes séparés non stables. Une base de données a besoin de l'inverse : une identité stable et son propre volume, toujours le même.

### Identité et ordre

Un StatefulSet nomme ses pods app-0, app-1, app-2, dans cet ordre, et les démarre séquentiellement. Chaque pod garde son nom et son volume à travers les redémarrages. C'est ce qui permet à un cluster de base de se reformer.

### Le service headless

Un service sans ClusterIP (clusterIP: None) donne un enregistrement DNS par pod : app-0.app.default.svc.cluster.local. Sans lui, pas d'identité réseau stable, et donc pas de réplication maître-esclave possible.

### La question à se poser

Un StatefulSet ne rend pas une base de données hautement disponible : il rend son identité stable. La réplication, le basculement, les sauvegardes restent à votre charge, ou à celle d'un opérateur dédié.


---

# Module 6 — Control plane et sécurité

## Les composants en détail

### etcd

Stockage clé/valeur, port 2379, quorum nécessaire. Trois nœuds minimum pour tolérer une panne. Une sauvegarde etcd non testée est une sauvegarde qui n'existe pas.

### API server

Trois étapes pour chaque requête : authentification (qui es-tu), autorisation (as-tu le droit), admission (le manifeste est-il acceptable). Comprendre cet ordre évite de chercher au mauvais endroit quand un déploiement est refusé.

### Scheduler

Il filtre les nœuds (ressources, taints, affinités), puis note les candidats. Un pod Pending avec un événement FailedScheduling vous dit précisément pourquoi : mémoire insuffisante, taint non toléré, volume non attachable.

### Controller manager

Une boucle par type d'objet : deployment, replicaset, node, endpoints, job. Chaque boucle compare l'état réel à l'état désiré et corrige. C'est la raison pour laquelle supprimer un pod d'un deployment ne change rien à long terme.

## RBAC

### Quatre objets

Role et ClusterRole définissent des permissions. RoleBinding et ClusterRoleBinding les accordent. Un Role vit dans un namespace, un ClusterRole est global. Le binding détermine la portée réelle.

### Ce qu'on écrit dedans

Des règles : apiGroups, resources, verbs. Par exemple pods en get, list, watch. Le verbe delete est distinct : un rôle lecture ne permet pas de supprimer, heureusement.

### Vérifier sans se tromper

kubectl auth can-i delete pods --as=system:serviceaccount:dev:builder -n dev répond oui ou non. C'est la seule façon fiable de vérifier, la lecture du YAML étant facile à mal interpréter.

### Les pièges

Un RoleBinding référence un Role du même namespace ; pour un ClusterRole, il peut être dans n'importe quel namespace. Un compte de service sans binding est authentifié mais n'a aucun droit, ce qui produit des erreurs 403 déroutantes.

## Sauvegarder et restaurer etcd

### Sauvegarder

ETCDCTL_API=3 etcdctl snapshot save /backup/etcd.db avec les certificats CA, client et clé. Vérifiez ensuite avec snapshot status : un fichier de la bonne taille ne prouve rien.

### Restaurer

etcdctl snapshot restore vers un nouveau data-dir, puis pointer le manifeste statique d'etcd vers ce répertoire, et redémarrer le pod statique. En cluster managé, cette manipulation est interdite : c'est le fournisseur qui sauvegarde.

### Le test qui compte

Une restauration chronométrée, sur un cluster de test, au moins une fois par trimestre. Noter la durée réelle, pas la durée théorique. C'est ce chiffre qui détermine votre RTO.

### La règle

Sauvegarde automatique, copie hors du cluster, chiffrement, et test régulier. Les quatre. Trois sur quatre ne suffisent pas le jour de l'incident.


---

# Module 7 — Cloud et production

## GKE et AKS

### Ce que le fournisseur gère

Le control plane, ses mises à jour, son intégration IAM et réseau. Vous gérez les nœuds, les charges de travail, les politiques. Cette frontière explique la moitié des questions de coût.

### Créer un cluster GKE

gcloud container clusters create demo --zone europe-west1-b --num-nodes 3. Puis gcloud container clusters get-credentials demo pour installer le contexte kubectl. Vérifiez toujours le contexte actif avant d'appliquer un manifeste.

### Node pools et autoscaling

Un node pool regroupe des nœuds de même taille. Le cluster autoscaler ajoute ou retire des nœuds selon les pods Pending. Le HPA, lui, ajoute des pods. Les deux se complètent, ils ne se remplacent pas.

### Le coût

Un control plane managé se paie, même sans charge. Les nœuds se paient à la seconde. Un cluster oublié pendant un week-end coûte plus cher que la formation. Surveillez, ou supprimez.

## Mises à jour et retours arrière

### La stratégie

RollingUpdate remplace les pods progressivement. maxSurge : combien de pods en plus pendant l'opération. maxUnavailable : combien peuvent manquer. Les deux valeurs pilotent la vitesse et le risque.

### Ce qui rend une mise à jour sans coupure

Une readiness probe correcte, et un nombre de replicas suffisant. Sans readiness, Kubernetes considère le nouveau pod prêt dès qu'il est démarré, et envoie du trafic à une application qui n'écoute pas encore.

### Revenir en arrière

kubectl rollout undo deployment/web revient à la révision précédente. rollout history liste les révisions. Pour revenir plus loin : --to-revision=2. L'historique est limité par revisionHistoryLimit.

### Protéger la disponibilité

Un PodDisruptionBudget garantit qu'un nombre minimum de pods reste disponible pendant une opération volontaire (drain, mise à jour de nœud). Il ne protège pas d'une panne, seulement des interruptions planifiées.

## Autoscaling

### Le HPA

HorizontalPodAutoscaler ajuste le nombre de replicas selon une métrique, le plus souvent le CPU. Il lui faut metrics-server, sinon il affiche unknown et ne fait rien.

### La condition d'un HPA qui marche

Chaque conteneur doit déclarer des requests CPU. Le HPA calcule un pourcentage de la request : sans request, il n'a pas de référence et reste aveugle. C'est l'erreur numéro un.

### VPA et cluster autoscaler

Le VPA ajuste les requests d'un pod, ce qui nécessite souvent un redémarrage. Le cluster autoscaler ajoute des nœuds quand des pods restent Pending. Empiler les trois sans mesure produit des oscillations.

### Mesurer avant d'autoscaler

Un HPA sur une application mal profilée ajoute des pods lents. Commencez par mesurer la latence et la consommation réelle, puis fixez des seuils qui correspondent à un comportement observé.


---

# Module 8 — Déboguer un cluster

## Les trois premiers réflexes

### Lire les événements

kubectl get events --sort-by=.lastTimestamp -n mon-ns. La plupart des pannes sont décrites là, en clair : image introuvable, quota dépassé, volume non monté.

### Décrire l'objet

kubectl describe pod mon-pod affiche l'état, les conditions, les derniers événements et les sondes en échec. C'est plus utile que les logs quand le conteneur ne démarre pas du tout.

### Lire les logs

kubectl logs mon-pod, et --previous pour le conteneur précédent quand il a redémarré. Sans --previous, vous lisez les logs du nouveau conteneur, qui est peut-être déjà en train de mourir.

### Vérifier le contexte

La moitié des 'ça ne marche pas' viennent d'un namespace ou d'un cluster différent. kubectl config view --minify affiche le contexte et le namespace actifs. Premier réflexe, avant toute analyse.

## Les pannes classiques

### ImagePullBackOff

Le nœud ne peut pas télécharger l'image : nom mal orthographié, tag inexistant, registre privé sans imagePullSecret. Vérifiez avec docker pull depuis le nœud, ou regardez l'événement Failed to pull image.

### CrashLoopBackOff

Le conteneur démarre puis meurt en boucle. Logs --previous obligatoires. Trois causes fréquentes : commande invalide, variable d'environnement manquante, application qui quitte immédiatement faute de configuration.

### Pending

Aucun nœud ne peut accueillir le pod. describe donne la raison : ressources insuffisantes, taint sans toleration, volume non disponible, affinité impossible. Ce n'est jamais un problème d'image.

### OOMKilled

La limite mémoire est atteinte, le noyau tue le conteneur. Augmenter la limite est un pansement : cherchez la fuite ou le pic. La sortie 137 dans describe est la signature de ce cas.

## Réseau et debug avancé

### Tester depuis l'intérieur

kubectl run tmp --rm -it --image=nicolaka/netshoot -- bash, puis curl, dig, nc. Tester depuis votre poste ne prouve rien : le chemin réseau n'est pas le même.

### kubectl debug

Un conteneur éphémère s'ajoute au pod sans le redémarrer : kubectl debug -it mon-pod --image=busybox. Indispensable sur une image distroless où aucun shell n'est disponible.

### Port-forward

kubectl port-forward svc/mon-service 8080:80 ouvre un tunnel local. C'est un outil de diagnostic, pas une exposition : il traverse vos droits et s'arrête avec votre session.

### Quand ça résiste

Si le DNS résout, que les endpoints existent et que la connexion échoue, regardez les NetworkPolicies, puis le plugin réseau, puis les règles iptables du nœud. Un tcpdump sur l'interface du pod tranche en trente secondes.


---

# QCM

## Module 1 — Du conteneur au cluster

**Q1. Quel composant stocke l'état complet du cluster ?**
- kubelet
- etcd ✅
- le scheduler
- kube-proxy

*Réponse : etcd. etcd est la mémoire du cluster. Le perdre sans sauvegarde, c'est perdre le cluster.*

**Q2. Que se passe-t-il si vous supprimez un pod géré par un Deployment ?**
- Rien, il est recréé ✅
- Le Deployment passe en erreur
- Le service s'arrête
- Le nœud redémarre

*Réponse : Rien, il est recréé. Le ReplicaSet recrée un pod pour revenir au nombre désiré. C'est la réconciliation.*

**Q3. Quel est le rôle du kubelet ?**
- Router le trafic entre pods
- Écrire dans etcd
- Piloter les conteneurs sur son nœud ✅
- Signer les certificats

*Réponse : Piloter les conteneurs sur son nœud. Le kubelet reçoit les PodSpec de l'API server et fait tourner les conteneurs via le runtime.*

**Q4. Un pod nu avec restartPolicy Always survit-il à la perte du nœud ?**
- Oui
- Non ✅
- Seulement avec un PVC
- Seulement en cloud

*Réponse : Non. Le pod nu n'est pas réordonnancé ailleurs. Il faut un ReplicaSet ou un Deployment pour cela.*

**Q5. Quelle commande bascule d'un cluster à l'autre ?**
- kubectl switch
- kubectl config use-context ✅
- kubectl cluster set
- kubectl context

*Réponse : kubectl config use-context. use-context change le contexte actif dans le kubeconfig.*

**Q6. Minikube sert à quoi ?**
- Cluster multi-nœuds de production
- Cluster local d'apprentissage ✅
- Registre d'images
- Supervision

*Réponse : Cluster local d'apprentissage. Un nœud local, suffisant pour apprendre et pour la plupart des exercices.*

**Q7. Quel objet garantit un nombre constant de pods identiques ?**
- Deployment
- ReplicaSet ✅
- StatefulSet
- DaemonSet

*Réponse : ReplicaSet. Le ReplicaSet assure le compte. Le Deployment l'enveloppe pour gérer les versions.*

**Q8. Que fait le controller-manager ?**
- Il expose l'API
- Il exécute les boucles de réconciliation ✅
- Il stocke l'état
- Il route le réseau

*Réponse : Il exécute les boucles de réconciliation. Un contrôleur par type d'objet, chacun compare l'état réel à l'état désiré.*

## Module 2 — Les objets de base

**Q1. Deux conteneurs dans le même pod partagent :**
- Le système de fichiers
- L'adresse IP et le réseau ✅
- Les limites CPU
- Le nom d'hôte externe

*Réponse : L'adresse IP et le réseau. Ils partagent le namespace réseau du pod, donc localhost, et peuvent partager des volumes.*

**Q2. Où se déclare le nombre de replicas d'un Deployment ?**
- spec.replicas ✅
- spec.template.replicas
- metadata.replicas
- status.replicas

*Réponse : spec.replicas. status.replicas est l'observation, spec.replicas l'intention.*

**Q3. Un Deployment ne crée aucun pod. Cause la plus probable ?**
- Image absente
- Sélecteur qui ne correspond pas aux labels ✅
- Pas de service
- Pas de namespace

*Réponse : Sélecteur qui ne correspond pas aux labels. Le sélecteur doit correspondre exactement aux labels du template. Sinon rien n'est adopté, sans erreur.*

**Q4. À quoi servent les annotations ?**
- À sélectionner des objets
- À stocker des métadonnées non sélectionnables ✅
- À remplacer les labels
- À chiffrer les données

*Réponse : À stocker des métadonnées non sélectionnables. Elles portent de l'information pour les outils, jamais pour la sélection.*

**Q5. Un namespace est-il une frontière de sécurité ?**
- Oui
- Non, c'est un cloisonnement logique ✅
- Oui, avec RBAC seulement
- Seulement en cloud

*Réponse : Non, c'est un cloisonnement logique. La sécurité vient du RBAC et des NetworkPolicies. Par défaut, les pods de deux namespaces communiquent.*

**Q6. Quelle commande montre pourquoi un pod ne démarre pas ?**
- kubectl logs
- kubectl describe pod ✅
- kubectl get pod
- kubectl top pod

*Réponse : kubectl describe pod. describe affiche les événements, donc la cause, même quand il n'y a pas de logs.*

**Q7. Que fait kubectl rollout undo ?**
- Supprime le deployment
- Revient à la révision précédente ✅
- Redémarre le cluster
- Annule un apply

*Réponse : Revient à la révision précédente. Il restaure le PodTemplate de la révision précédente.*

**Q8. Combien de conteneurs applicatifs dans un pod en pratique ?**
- Un seul, le plus souvent ✅
- Toujours trois
- Jamais plus de deux
- Autant qu'on veut sans limite

*Réponse : Un seul, le plus souvent. Le pod est l'unité de placement : plusieurs conteneurs applicatifs dedans compliquent le scaling.*

## Module 3 — Réseau

**Q1. Un Service ClusterIP est joignable :**
- Depuis Internet
- Depuis le cluster uniquement ✅
- Depuis le nœud seulement
- Depuis un autre cluster

*Réponse : Depuis le cluster uniquement. C'est le type par défaut, interne au cluster.*

**Q2. Que signifie des endpoints vides pour un Service ?**
- Le service est supprimé
- Le sélecteur ne correspond à aucun pod prêt ✅
- Le port est fermé
- Le DNS est cassé

*Réponse : Le sélecteur ne correspond à aucun pod prêt. Pas d'endpoints = pas de pod prêt correspondant au sélecteur.*

**Q3. port et targetPort : lequel désigne le conteneur ?**
- port
- targetPort ✅
- nodePort
- hostPort

*Réponse : targetPort. port est celui du Service, targetPort celui du conteneur.*

**Q4. Un Ingress fonctionne sans contrôleur ?**
- Oui
- Non ✅
- Seulement en cloud
- Seulement avec TLS

*Réponse : Non. L'objet est une configuration lue par un contrôleur qui fait le vrai travail de proxy.*

**Q5. Quel type de Service donne un nom DNS par pod ?**
- ClusterIP
- NodePort
- Headless (clusterIP: None) ✅
- LoadBalancer

*Réponse : Headless (clusterIP: None). Un service headless publie un enregistrement par pod, indispensable aux StatefulSets.*

**Q6. Une NetworkPolicy sans plugin réseau compatible :**
- Bloque tout
- N'a aucun effet ✅
- Provoque une erreur
- S'applique partiellement

*Réponse : N'a aucun effet. La politique est stockée mais non appliquée : faux sentiment de sécurité.*

**Q7. Forme DNS complète d'un service ?**
- service.namespace.svc.cluster.local ✅
- namespace.service.local
- service.cluster.local
- svc.service.namespace

*Réponse : service.namespace.svc.cluster.local. C'est l'ordre attendu par CoreDNS.*

**Q8. Un 503 renvoyé par l'ingress signifie le plus souvent :**
- Chemin inconnu
- Service sans endpoints prêts ✅
- Certificat expiré
- DNS cassé

*Réponse : Service sans endpoints prêts. 404 = pas de règle, 503 = règle présente mais backend indisponible.*

## Module 4 — Configuration et ressources

**Q1. Un Secret Kubernetes est par défaut :**
- Chiffré en base
- Encodé en base64 ✅
- Haché
- Stocké hors cluster

*Réponse : Encodé en base64. base64 est un encodage réversible, pas un chiffrement.*

**Q2. Un ConfigMap monté en fichier est mis à jour :**
- Jamais
- Automatiquement dans le pod ✅
- Au redémarrage seulement
- Uniquement en cloud

*Réponse : Automatiquement dans le pod. Le kubelet synchronise le volume ; l'application doit relire le fichier pour en profiter.*

**Q3. Liveness probe échoue : que fait Kubernetes ?**
- Retire le pod des endpoints
- Tue et relance le conteneur ✅
- Met le pod en Pending
- Augmente la mémoire

*Réponse : Tue et relance le conteneur. Échec de liveness = redémarrage. C'est readiness qui retire du trafic.*

**Q4. Sans readiness probe, un déploiement :**
- Est plus rapide
- Peut envoyer du trafic à un pod non prêt ✅
- Ne démarre pas
- Perd ses logs

*Réponse : Peut envoyer du trafic à un pod non prêt. Le pod est considéré prêt dès que le conteneur tourne.*

**Q5. Limite mémoire dépassée :**
- Throttling
- OOMKilled ✅
- Pending
- Éviction du nœud

*Réponse : OOMKilled. Le noyau tue le processus. Le throttling concerne le CPU.*

**Q6. Limite CPU dépassée :**
- Le conteneur est tué
- Le conteneur est ralenti ✅
- Le pod redémarre
- Le nœud s'éteint

*Réponse : Le conteneur est ralenti. Le CPU est bridé par le CFS, sans arrêt du conteneur.*

**Q7. Sans requests, que fait le scheduler ?**
- Il refuse le pod
- Il place sans base fiable ✅
- Il attend
- Il crée un nœud

*Réponse : Il place sans base fiable. Il n'a pas de référence de besoin, donc la répartition est arbitraire.*

**Q8. Quelle classe QoS est évincée en premier ?**
- Guaranteed
- Burstable
- BestEffort ✅
- Toutes égales

*Réponse : BestEffort. BestEffort n'a aucune request, donc aucune protection.*

## Module 5 — Stockage

**Q1. Un emptyDir survit-il au redémarrage du pod ?**
- Oui
- Non ✅
- Selon le nœud
- Selon la taille

*Réponse : Non. Il est détruit avec le pod. Pour survivre, il faut un PVC.*

**Q2. Que fait un PVC ?**
- Crée un pod
- Demande un volume selon taille et mode d'accès ✅
- Formate un disque
- Chiffre les données

*Réponse : Demande un volume selon taille et mode d'accès. Le PVC est une demande ; le PV est la ressource fournie.*

**Q3. ReadWriteOnce signifie :**
- Un pod en écriture
- Un seul nœud en écriture ✅
- Un seul namespace
- Lecture seule

*Réponse : Un seul nœud en écriture. RWO est par nœud, pas par pod : deux pods sur le même nœud peuvent le monter.*

**Q4. reclaimPolicy Retain :**
- Supprime le volume avec le PVC
- Conserve le volume après suppression du PVC ✅
- Le rend public
- Le chiffre

*Réponse : Conserve le volume après suppression du PVC. Les données restent, à vous de les récupérer ou de les supprimer.*

**Q5. Un StatefulSet garantit :**
- La haute disponibilité
- Une identité stable par pod ✅
- Le chiffrement
- L'autoscaling

*Réponse : Une identité stable par pod. Noms stables, ordre de démarrage, volume par pod. La HA reste à votre charge.*

**Q6. Pourquoi un service headless avec un StatefulSet ?**
- Pour exposer sur Internet
- Pour donner un DNS par pod ✅
- Pour éviter les labels
- Pour le TLS

*Réponse : Pour donner un DNS par pod. Sans identité réseau par pod, la réplication ne peut pas se coordonner.*

**Q7. hostPath est dangereux parce que :**
- Il est lent
- Le pod écrit sur le nœud et dépend d'un nœud précis ✅
- Il coûte cher
- Il n'est pas supporté

*Réponse : Le pod écrit sur le nœud et dépend d'un nœud précis. Le pod devient dépendant du nœud et peut altérer le système hôte.*

**Q8. Sans StorageClass, comment obtenir un PV ?**
- Automatiquement
- En le créant à la main ✅
- Impossible
- Via un ConfigMap

*Réponse : En le créant à la main. Le provisionnement dynamique nécessite une StorageClass.*

## Module 6 — Control plane et sécurité

**Q1. Quel port utilise etcd ?**
- 6443
- 2379 ✅
- 10250
- 53

*Réponse : 2379. 2379 pour les clients, 2380 pour le pair-à-pair.*

**Q2. Combien de nœuds etcd pour tolérer une panne ?**
- Un
- Deux
- Trois ✅
- Cinq

*Réponse : Trois. Trois nœuds tolèrent la perte d'un seul membre, grâce au quorum.*

**Q3. Un RoleBinding peut-il référencer un ClusterRole ?**
- Non
- Oui, avec portée limitée au namespace du binding ✅
- Seulement en cloud
- Seulement pour les pods

*Réponse : Oui, avec portée limitée au namespace du binding. Le ClusterRole définit les droits, le RoleBinding les limite à un namespace.*

**Q4. Quelle commande vérifie un droit sans l'exercer ?**
- kubectl auth can-i ✅
- kubectl get role
- kubectl describe sa
- kubectl rbac check

*Réponse : kubectl auth can-i. can-i, avec --as pour simuler un compte de service.*

**Q5. Après restauration d'etcd, que faut-il faire ?**
- Rien, c'est automatique
- Pointer le manifeste statique vers le nouveau data-dir ✅
- Redémarrer tous les pods
- Recréer le cluster

*Réponse : Pointer le manifeste statique vers le nouveau data-dir. Le pod statique etcd doit utiliser le répertoire restauré.*

**Q6. Où sont stockés les manifests des pods statiques ?**
- /var/lib/etcd
- /etc/kubernetes/manifests ✅
- /etc/cni
- /var/log/pods

*Réponse : /etc/kubernetes/manifests. Le kubelet surveille ce répertoire et recrée les pods correspondants.*

**Q7. Un compte de service sans binding :**
- A tous les droits
- Est authentifié sans droits ✅
- N'existe pas
- Est administrateur

*Réponse : Est authentifié sans droits. Il obtient un 403 : il est reconnu, mais rien ne l'autorise.*

**Q8. Lequel n'est PAS une étape de l'API server ?**
- Authentification
- Autorisation
- Admission
- Réplication ✅

*Réponse : Réplication. La réplication est le travail des contrôleurs.*

## Module 7 — Cloud et production

**Q1. Sur GKE, qui gère le control plane ?**
- Vous
- Google ✅
- Le kubelet
- Le scheduler local

*Réponse : Google. C'est la différence de fond avec un cluster auto-hébergé.*

**Q2. maxUnavailable contrôle :**
- Le nombre de pods en plus
- Le nombre de pods manquants autorisés ✅
- La vitesse réseau
- Le nombre de nœuds

*Réponse : Le nombre de pods manquants autorisés. maxSurge ajoute, maxUnavailable retire : les deux bornent la perturbation.*

**Q3. Sans readiness, une mise à jour provoque :**
- Rien
- Des erreurs pendant le basculement ✅
- Un rollback automatique
- Un redémarrage du nœud

*Réponse : Des erreurs pendant le basculement. Le trafic part vers des pods qui n'écoutent pas encore.*

**Q4. Que fait un PodDisruptionBudget ?**
- Bloque les pannes
- Garantit un minimum de pods pendant une opération volontaire ✅
- Accélère le drain
- Supprime les pods

*Réponse : Garantit un minimum de pods pendant une opération volontaire. Il protège des interruptions planifiées, pas des incidents.*

**Q5. Le HPA a besoin de :**
- Un Ingress
- metrics-server et des requests ✅
- Un PVC
- Un DaemonSet

*Réponse : metrics-server et des requests. Sans métriques ni requests, il affiche unknown et ne fait rien.*

**Q6. Qui ajoute des nœuds quand des pods restent Pending ?**
- HPA
- VPA
- Cluster autoscaler ✅
- kube-proxy

*Réponse : Cluster autoscaler. Le HPA ajoute des pods, le cluster autoscaler ajoute des nœuds.*

**Q7. rollout undo sans --to-revision :**
- Revient à la première version
- Revient à la précédente ✅
- Supprime tout
- Échoue

*Réponse : Revient à la précédente. Il recule d'une révision.*

**Q8. Un cluster managé oublié coûte :**
- Rien
- Le control plane et les nœuds ✅
- Seulement le stockage
- Seulement le réseau

*Réponse : Le control plane et les nœuds. Le control plane est facturé même sans charge.*

## Module 8 — Déboguer un cluster

**Q1. Un conteneur redémarre en boucle : quels logs lire ?**
- kubectl logs
- kubectl logs --previous ✅
- kubectl describe node
- kubectl top pod

*Réponse : kubectl logs --previous. --previous lit le conteneur qui vient de mourir.*

**Q2. ImagePullBackOff signifie :**
- Crash applicatif
- Le nœud ne peut pas télécharger l'image ✅
- Mémoire insuffisante
- Sonde en échec

*Réponse : Le nœud ne peut pas télécharger l'image. Nom, tag, registre privé : l'événement le précise.*

**Q3. Pending signifie :**
- Le conteneur crash
- Aucun nœud ne peut accueillir le pod ✅
- Le service est absent
- Le DNS est cassé

*Réponse : Aucun nœud ne peut accueillir le pod. describe affiche FailedScheduling et sa raison.*

**Q4. Code de sortie 137 :**
- Erreur applicative
- OOMKilled ou SIGKILL ✅
- Arrêt propre
- Timeout

*Réponse : OOMKilled ou SIGKILL. 128 + 9 : le processus a été tué.*

**Q5. Quel outil ajoute un conteneur de debug à un pod existant ?**
- kubectl exec
- kubectl debug ✅
- kubectl attach
- kubectl cp

*Réponse : kubectl debug. Le conteneur éphémère s'ajoute sans redémarrer le pod.*

**Q6. Tester un service depuis votre poste :**
- Prouve que le réseau du cluster fonctionne
- Ne prouve rien du chemin interne ✅
- Remplace un pod de test
- Suffit toujours

*Réponse : Ne prouve rien du chemin interne. Le chemin réseau n'est pas le même ; testez depuis un pod.*

**Q7. Les NetworkPolicies sont appliquées par :**
- kube-proxy
- Le plugin réseau (CNI) ✅
- Le scheduler
- CoreDNS

*Réponse : Le plugin réseau (CNI). Sans implémentation côté CNI, la politique est stockée mais inerte.*

**Q8. Premier réflexe devant un 'ça ne marche pas' :**
- Redémarrer le cluster
- Vérifier contexte et namespace ✅
- Supprimer le pod
- Réinstaller kubectl

*Réponse : Vérifier contexte et namespace. La moitié des cas viennent du mauvais contexte ou du mauvais namespace.*


---

# Labs

## Premier cluster

Démarrez un cluster local, vérifiez le nœud, listez les pods système.

```
minikube start
kubectl get nodes
kubectl get pods -A
```

**Validation :** Un nœud Ready et les pods système en Running.

## Déployer et exposer

Créez un Deployment nginx à 3 replicas, exposez-le en ClusterIP, vérifiez les endpoints.

```
kubectl create deployment web --image=nginx --replicas=3
kubectl expose deployment web --port=80
kubectl get endpoints web
```

**Validation :** 3 pods Running et 3 adresses dans les endpoints.

## Mise à jour et retour arrière

Changez l'image pour nginx:1.27, suivez le rollout, puis revenez à la version précédente.

```
kubectl set image deployment/web nginx=nginx:1.27
kubectl rollout status deployment/web
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
```

**Validation :** Deux révisions visibles et retour à la première.

## Ingress local

Activez l'addon ingress sur minikube et exposez web sur web.local.

```
minikube addons enable ingress
kubectl create ingress web --rule="web.local/*=web:80"
```

**Validation :** curl avec l'en-tête Host renvoie la page nginx.

## Configuration et sondes

Créez un ConfigMap, injectez-le en variable, ajoutez une readiness sur /, puis cassez le chemin pour observer.

```
kubectl create configmap app --from-literal=MODE=prod
# monter en env puis readinessProbe httpGet path: /nope
kubectl describe pod
```

**Validation :** Le pod devient NotReady et sort des endpoints.

## Volume persistant

Créez un PVC de 1Gi, montez-le dans un pod, écrivez un fichier, supprimez le pod, recréez-le.

```
kubectl create -f pvc.yaml
kubectl run writer --image=busybox --overrides=... -- sh -c 'echo ok > /data/f'
# recréer et cat /data/f
```

**Validation :** Le fichier est toujours là après recréation.

## StatefulSet

Déployez un StatefulSet à 3 replicas avec un service headless et vérifiez les noms DNS.

```
kubectl apply -f sts.yaml
kubectl get pods -l app=db
kubectl run tmp --rm -it --image=busybox -- nslookup db-0.db
```

**Validation :** db-0, db-1, db-2 répondent chacun à leur nom.

## RBAC minimal

Créez un compte de service qui peut seulement lister les pods dans dev, et vérifiez.

```
kubectl create sa reader -n dev
kubectl create role podreader --verb=list --resource=pods -n dev
kubectl create rolebinding rb --role=podreader --serviceaccount=dev:reader -n dev
kubectl auth can-i list pods --as=system:serviceaccount:dev:reader -n dev
```

**Validation :** Oui pour list, non pour delete.

## Sauvegarde etcd

Prenez un snapshot etcd avec les certificats, puis vérifiez son intégrité.

```
ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd.db \
 --endpoints=https://127.0.0.1:2379 \
 --cacert=/etc/kubernetes/pki/etcd/ca.crt \
 --cert=/etc/kubernetes/pki/etcd/server.crt \
 --key=/etc/kubernetes/pki/etcd/server.key
ETCDCTL_API=3 etcdctl snapshot status /tmp/etcd.db
```

**Validation :** Le status affiche un hash et un nombre de clés cohérent.

## Diagnostic guidé

Provoquez un CrashLoopBackOff, puis un Pending, et trouvez la cause de chacun sans aide.

```
# image inexistante puis ressources énormes
kubectl describe pod
kubectl get events --sort-by=.lastTimestamp
```

**Validation :** Vous nommez la cause exacte dans les deux cas, à partir des événements.


---

# Fiches de commandes

## Objets et commandes
- **Lister** — `kubectl get pods,deploy,svc,ing -A`
- **Détail** — `kubectl describe pod NAME -n NS`
- **YAML** — `kubectl get deploy NAME -o yaml`
- **Appliquer** — `kubectl apply -f file.yaml`
- **Supprimer** — `kubectl delete -f file.yaml`

## Déploiement
- **Créer** — `kubectl create deployment web --image=nginx --replicas=3`
- **Exposer** — `kubectl expose deployment web --port=80 --type=ClusterIP`
- **Changer l'image** — `kubectl set image deployment/web nginx=nginx:1.27`
- **Suivre** — `kubectl rollout status deployment/web`
- **Revenir** — `kubectl rollout undo deployment/web`

## Diagnostic
- **Événements** — `kubectl get events --sort-by=.lastTimestamp`
- **Logs précédents** — `kubectl logs POD --previous`
- **Entrer** — `kubectl exec -it POD -- sh`
- **Debug** — `kubectl debug -it POD --image=busybox`
- **Tunnel** — `kubectl port-forward svc/NAME 8080:80`

## Réseau
- **Endpoints** — `kubectl get endpoints NAME`
- **DNS** — `kubectl run tmp --rm -it --image=busybox -- nslookup NAME`
- **Policies** — `kubectl get networkpolicy -A`
- **Ingress** — `kubectl get ingress -A`

## Stockage
- **PVC** — `kubectl get pvc`
- **PV** — `kubectl get pv`
- **Classes** — `kubectl get storageclass`
- **Monter** — `volumes: [{name: d, persistentVolumeClaim: {claimName: c}}]`

## Sécurité
- **Tester un droit** — `kubectl auth can-i delete pods --as=system:serviceaccount:dev:sa -n dev`
- **Rôles** — `kubectl get role,clusterrole -A`
- **Bindings** — `kubectl get rolebinding,clusterrolebinding -A`
- **Secrets** — `kubectl get secret NAME -o jsonpath='{.data}'`


---

# Méthode

## Comment suivre cette formation

### Le parcours

Huit modules, du conteneur au diagnostic. Suivez-les dans l'ordre : chaque module réutilise les objets du précédent. Comptez 6 à 8 heures de lecture et autant de pratique.

### Le rythme conseillé

Un module par jour, puis les labs du module le même jour. Lire sans taper ne fixe rien : la main retient ce que l'œil oublie.

### La validation

Chaque module a son QCM. 80 pour cent de réussite est le seuil raisonnable avant de passer au suivant. En dessous, relisez les leçons du module.

### Le certificat

Il se génère depuis l'écran d'accueil quand tous les modules sont lus et les QCM réussis. Il porte votre nom, la date et le détail des modules validés. Il atteste d'une formation suivie, pas d'une certification officielle Kubernetes.

## Prérequis et outillage

### Ce qu'il faut savoir

Docker (image, conteneur, volume, réseau) et Git. Des bases Linux : se déplacer, éditer un fichier, lire un log. Le reste est enseigné ici.

### Ce qu'il faut installer

kubectl, minikube ou kind, et un éditeur. Rien d'autre : pas de compte cloud nécessaire pour les modules 1 à 6.

### La machine

8 Go de RAM suffisent pour minikube avec 2 Go alloués. 4 cœurs rendent les labs plus confortables. Un disque avec 20 Go libres évite les mauvaises surprises.

### Le cloud

Le module 7 utilise GKE ou AKS. Un compte d'essai suffit, mais pensez à supprimer le cluster après : le control plane est facturé même à l'arrêt des charges.

## Méthode de travail

### Toujours par le YAML

Les commandes impératives (kubectl run, create deployment) servent à apprendre et à dépanner. En production, tout passe par un manifeste versionné dans Git. C'est la seule façon de savoir ce qui tourne.

### Lire avant d'appliquer

kubectl diff -f manifest.yaml montre ce qui va changer. Sur un cluster qui compte, c'est la différence entre une mise à jour et un incident.

### Nommer pour retrouver

Un préfixe par équipe, un label app et un label version. Sans ces trois, le premier kubectl get pods -A devient illisible au bout de trois semaines.

### Détruire ce qu'on crée

Chaque lab doit finir par un nettoyage. Un cluster d'apprentissage qui accumule les objets finit par saturer, et vous passerez une soirée à chercher pourquoi un pod reste Pending.

## À propos du certificat

### Ce qu'il atteste

Avoir parcouru l'intégralité des huit modules et réussi les QCM. C'est une attestation de formation, délivrée localement par cette application.

### Ce qu'il n'est pas

Ni le CKA, ni le CKAD, ni aucune certification officielle. Ces examens se passent chez la Linux Foundation, sur un cluster réel, et ne s'obtiennent pas en lisant.

### Comment l'obtenir

Terminez tous les modules, puis ouvrez l'écran d'accueil : le bouton de certificat apparaît. Saisissez votre nom, imprimez ou enregistrez en PDF.

### La suite logique

Après cette formation, un entraînement CKA sur cluster réel est la bonne étape. Le vocabulaire sera acquis, il restera la vitesse et les réflexes en conditions de temps limité.
