output "cluster_name" {
  value = kind_cluster.statuswatch.name
}

output "kubeconfig_path" {
  value = kind_cluster.statuswatch.kubeconfig_path
}