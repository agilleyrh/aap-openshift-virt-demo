# AAP OpenShift and OpenShift Virtualization Demo

Ansible Automation Platform content for demonstrating how AAP can **audit** and **fully manage** OpenShift clusters and OpenShift Virtualization (CNV) workloads through the Kubernetes API.

## Repository layout

### Audit playbooks (read-only)

```
playbooks/openshift/               # Cluster health, operators, projects, routes
playbooks/openshift-virt/          # CNV status, VM inventory, storage, templates
```

### Management playbooks (mutating)

```
playbooks/openshift-admin/
  01-ensure-demo-project.yml       # Create/labeled demo project
  02-deploy-sample-application.yml # Deploy UBI httpd deployment + service
  03-expose-service-route.yml      # Create edge TLS route
  04-apply-network-policy.yml      # Namespace network policy
  05-configure-resource-quota.yml  # Quota and limit range
  06-create-service-account-rbac.yml
  07-scale-application.yml         # Scale deployment replicas
  08-check-cluster-updates.yml     # ClusterVersion and available updates
  09-install-cluster-operator.yml  # Install NMState operator (configurable)
  10-manage-route-networking.yml   # Route annotations and TLS tuning

playbooks/cnv-admin/
  01-ensure-virt-namespace.yml
  02-create-virtual-machine.yml
  03-start-virtual-machine.yml
  04-stop-virtual-machine.yml
  05-restart-virtual-machine.yml
  06-patch-vm-resources.yml
  07-create-blank-datavolume.yml
  08-delete-virtual-machine.yml
```

Shared variables live in `playbooks/vars/demo.yml` and `playbooks/vars/admin.yml`.

## Prerequisites

- Ansible Automation Platform 2.4+ with `kubernetes.core` in the execution environment
- **OpenShift knmpg Cluster** credential attached to each job template
- Cluster-admin token for management playbooks

## Configure AAP

```bash
export AAP_MCP_TOKEN=<aap-token>
export OCP_TOKEN=<openshift-token>
python3 scripts/configure_aap.py
```

This creates job templates and workflows in the **Default** organization.

## Audit workflows

| Workflow | Purpose |
|----------|---------|
| WF - OpenShift Platform Audit | Read-only OpenShift cluster audit |
| WF - OpenShift Virtualization Audit | Read-only CNV/VM audit |
| WF - OpenShift Virtualization Bootstrap and Audit | Install CNV, then audit |
| WF - Full OpenShift and Virt Demo | Complete read-only story |

## Management workflows

| Workflow | Purpose |
|----------|---------|
| WF - OpenShift App Deploy and Expose | Project → app → route → route tuning |
| WF - OpenShift Governance and RBAC | NetworkPolicy, quota, RBAC |
| WF - OpenShift Operator and Updates | Cluster updates + operator install |
| WF - CNV Virtual Machine Lifecycle | Create → start → resize → stop VM |
| WF - Full Platform Management Demo | OpenShift app deployment + CNV lifecycle |

## Suggested management demo flow

1. **WF - OpenShift App Deploy and Expose** — show project creation, workload deployment, public route
2. **WF - OpenShift Governance and RBAC** — network policy, quotas, least-privilege SA
3. **WF - OpenShift Operator and Updates** — available cluster updates + NMState operator install
4. **WF - CNV Virtual Machine Lifecycle** — full VM day-2 operations via AAP

Override variables at launch with extra vars, for example:

```yaml
demo_namespace: aap-demo
demo_replicas: 3
virt_vm_name: aap-managed-cirros
operator_package: kubernetes-nmstate-operator
```

## License

Apache-2.0
