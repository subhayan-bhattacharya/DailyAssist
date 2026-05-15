output "project_id" {
  value = neon_project.language_learning.id
}

output "database_name" {
  value = neon_database.language_learning.name
}

output "role_name" {
  value = neon_role.app_owner.name
}

output "role_password" {
  value     = neon_role.app_owner.password
  sensitive = true
}

output "connection_uri" {
  value     = neon_project.language_learning.connection_uri
  sensitive = true
}

output "app_connection_uri" {
  value     = "postgres://${neon_role.app_owner.name}:${neon_role.app_owner.password}@${neon_project.language_learning.database_host}/${neon_database.language_learning.name}"
  sensitive = true
}
