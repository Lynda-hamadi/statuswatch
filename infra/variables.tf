variable "cluster_name" {
  description = "Nom du cluster kind"
  type        = string
  default     = "statuswatch"
}

variable "kubeconfig_path" {
  description = "Fichier où écrire l'accès au cluster (séparé de ton kubeconfig par défaut)"
  type        = string
  default     = "~/.kube/statuswatch-config"
}