terraform {
  required_providers {
    proxmox = {
      source = "bpg/proxmox"
      version = "0.71.0"
    }
  }
}


provider "proxmox" {

  endpoint = "https://192.168.1.47:8006"
  username = "root@pam"
  password = "cl0ser2g0d"
  insecure = true
  # uncomment (unless on Windows...)
  tmp_dir  = "/var/tmp"

  ssh {
    agent = true
  }
}
resource "proxmox_virtual_environment_container" "github-runner-lab" {
  node_name  = "pve-heavy"
  hostname     = "github-runner-lab"
  ostemplate   = "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst"
  unprivileged = false
  password     = "cl0ser2g0d"
  onboot       = true
  vm_id         = 400
  start        = true
  memory       = 4096
  ostype       = "ubuntu"
  // Terraform will crash without rootfs defined
  rootfs {
    storage = "zfs-ssd"
    size    = "30G"
  }

  network {
    name   = "eth0"
    bridge = "vmbr0"
    ip     = "192.168.1.15/24"
  }
}