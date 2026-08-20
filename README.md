# AAP OpenShift and OpenShift Virtualization Demo

Read-only Ansible Automation Platform content for demonstrating how AAP can audit and manage OpenShift clusters and OpenShift Virtualization (KubeVirt/CNV) workloads.

All playbooks use **`kubernetes.core.k8s_info`** and other read-only modules. Nothing in this repository creates, updates, or deletes cluster resources.

## Research basis

This content is based on Red Hat and community guidance, including:

- [kubernetes.core collection](https://github.com/ansible-collections/kubernetes.core)
- [Ansible Content Collection for Red Hat OpenShift (`redhat.openshift`)](https://www.redhat.com/en/blog/introducing-the-ansible-content-collection-for-red-hat-openshift)
- [AAP for OpenShift Virtualization in multi-cluster environments](https://www.redhat.com/en/blog/ansible-automation-platform-openshift-virtualization-multi-cluster-environment)
- Community references such as [openshift-virt-ansible-automation](https://github.com/tosin2013/openshift-virt-ansible-automation) and [awx-kubevirt-demo](https://codeberg.org/jlh/awx-kubevirt-demo)

## Repository layout

```
playbooks/openshift/
  01-cluster-overview.yml          # Nodes, cluster version
  02-cluster-operators.yml         # ClusterOperator health
  03-projects-and-quotas.yml       # Projects, quotas, limits
  04-workload-health.yml           # Deployments/pods in key namespaces
  05-routes-and-ingress.yml        # Routes and ingress controllers

playbooks/openshift-virt/
  01-cnv-operator-status.yml       # CNV/HyperConverged operator status
  02-virtual-machines-inventory.yml
  03-vm-instances-status.yml       # Running VMIs
  04-storage-and-datavolumes.yml   # DataVolumes and virt PVCs
  05-vm-templates-inventory.yml    # Instance types and templates
```

## Prerequisites

- Ansible Automation Platform 2.4+ with `kubernetes.core` in the execution environment
- OpenShift or Kubernetes API credential attached to each job template
- Cluster admin or read-only RBAC (`cluster-reader` + virt view permissions)

### Credential

Attach an **OpenShift or Kubernetes API Bearer Token** credential with:

- **Host:** `https://api.<cluster>:6443`
- **Bearer token:** valid service account or user token
- **Verify SSL:** enabled (provide CA if needed)

AAP injects `K8S_AUTH_HOST`, `K8S_AUTH_API_KEY`, and related variables automatically.

## Local testing

```bash
export K8S_AUTH_HOST="https://api.cluster.example:6443"
export K8S_AUTH_API_KEY="<token>"
export K8S_AUTH_VERIFY_SSL=yes

ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/openshift/01-cluster-overview.yml
```

## OpenShift Virtualization note

If OpenShift Virtualization is not installed, virt playbooks exit gracefully and report that CNV CRDs are missing. Install the **kubevirt-hyperconverged** operator to populate VM inventory playbooks.

## Demo workflows in AAP

Three workflow job templates are created in the **Default** organization:

1. **WF - OpenShift Platform Audit** — all `playbooks/openshift/*` jobs
2. **WF - OpenShift Virtualization Audit** — all `playbooks/openshift-virt/*` jobs
3. **WF - Full OpenShift and Virt Demo** — platform audit, then virtualization audit

## License

Apache-2.0
