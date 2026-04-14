# Parefeu serveur IA

## Problématique

Un port était inutilement ouvert sur le serveur.
Pour en savoir plus sur ce serveur : https://github.com/betagouv/portail-rse/discussions/427

On a besoin que des protocoles SSH et HTTPS en entrée. Plusieurs parefeux possibles

## Solution envisagée

### Iptables

L'outil historique.


### Nftables

L'outil qui a remplacé Iptables.


### Firewalld

L'outil qui est aujourd'hui privilégié.
https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/configuring_firewalls_and_packet_filters/index

## Choix

Firewall-cmd est simple et permet d'enregistrer directement la configuration.

On autorise uniquement SSH, HTTPS et le `ping` si jamais on en a besoin.

```sh
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --add-service=ssh --permanent

# --add-icmp-block-inversion uniquement si `icmp-block-inversion: no`
# dans la commande `firewall-cmd --list-all`
sudo firewall-cmd --add-icmp-block-inversion --permanent

sudo firewall-cmd --add-icmp-block=echo-reply --permanent
sudo firewall-cmd --add-icmp-block=echo-request --permanent
sudo firewall-cmd --set-target=DROP --permanent

sudo firewall-cmd --reload
```
