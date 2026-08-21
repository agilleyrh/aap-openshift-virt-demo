#!/usr/bin/env python3
"""Configure AAP job template surveys for OpenShift and CNV demo content."""
import json
import os
import ssl
import urllib.parse
import urllib.request

AAP_URL = os.environ.get("AAP_CONTROLLER_URL", "https://aap-aap.apps.cluster-knmpg.dyn.redhatworkshops.io")
TOKEN = os.environ["AAP_MCP_TOKEN"]
ORG_ID = 1
PROJECT_ID = 125

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def api(method, path, data=None):
    url = f"{AAP_URL}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def q_text(variable, question_name, default="", required=False, description=""):
    return {
        "variable": variable,
        "question_name": question_name,
        "question_description": description,
        "type": "text",
        "required": required,
        "default": default,
    }


def q_integer(variable, question_name, default, required=False, description=""):
    return {
        "variable": variable,
        "question_name": question_name,
        "question_description": description,
        "type": "integer",
        "required": required,
        "default": int(default),
    }


def q_choice(variable, question_name, choices, default, required=False, description=""):
    return {
        "variable": variable,
        "question_name": question_name,
        "question_description": description,
        "type": "multiplechoice",
        "required": required,
        "default": default,
        "choices": choices,
    }


def q_multiselect(variable, question_name, choices, default, required=False, description=""):
    return {
        "variable": variable,
        "question_name": question_name,
        "question_description": description,
        "type": "multiselect",
        "required": required,
        "default": default,
        "choices": choices,
    }


NS_CHOICES = [
    "openshift",
    "aap",
    "kube-system",
    "default",
    "virt-demo",
    "openshift-cnv",
    "aap-demo",
    "openshift-nmstate",
]

SURVEYS = {
    "OCP Demo - Cluster Overview": {
        "name": "Cluster Overview Survey",
        "description": "Optional filters for the cluster overview report.",
        "spec": [
            q_choice(
                "include_node_roles",
                "Include Node Role Details",
                ["yes", "no"],
                "yes",
                True,
                "Include control-plane/worker role labels in node output.",
            ),
        ],
    },
    "OCP Demo - Cluster Operators": {
        "name": "Cluster Operators Survey",
        "description": "Filter operator health output.",
        "spec": [
            q_choice(
                "show_healthy_operators",
                "Show Healthy Operators",
                ["yes", "no"],
                "yes",
                True,
                "When set to no, only degraded or unavailable operators are highlighted.",
            ),
        ],
    },
    "OCP Demo - Projects and Quotas": {
        "name": "Projects Survey",
        "description": "Project and quota reporting options.",
        "spec": [
            q_text(
                "project_name_filter",
                "Project Name Contains",
                "",
                False,
                "Optional substring filter for project names (leave blank for all).",
            ),
        ],
    },
    "OCP Demo - Workload Health": {
        "name": "Workload Health Survey",
        "description": "Choose namespaces to inspect for workload health.",
        "spec": [
            q_multiselect(
                "target_namespaces",
                "Target Namespaces",
                NS_CHOICES,
                "openshift\naap\nkube-system\naap-demo",
                True,
                "Namespaces scanned for Deployments and Pods.",
            ),
        ],
    },
    "OCP Demo - Routes and Ingress": {
        "name": "Routes Survey",
        "description": "Filter route reporting.",
        "spec": [
            q_text(
                "route_namespace_filter",
                "Route Namespace Filter",
                "",
                False,
                "Optional namespace name to limit route listing (blank = all routes).",
            ),
        ],
    },
    "OCP Virt Demo - Install CNV": {
        "name": "Install CNV Survey",
        "description": "Configure OpenShift Virtualization installation.",
        "spec": [
            q_text("cnv_namespace", "CNV Namespace", "openshift-cnv", True),
            q_text("cnv_channel", "Operator Channel", "stable", True),
            q_text("cnv_package", "Operator Package", "kubevirt-hyperconverged", True),
        ],
    },
    "OCP Virt Demo - CNV Operator Status": {
        "name": "CNV Status Survey",
        "description": "CNV operator reporting scope.",
        "spec": [
            q_text("cnv_operator_namespace", "CNV Namespace", "openshift-cnv", True),
        ],
    },
    "OCP Virt Demo - VM Inventory": {
        "name": "VM Inventory Survey",
        "description": "Scope VM inventory reporting.",
        "spec": [
            q_choice("virt_scope", "Inventory Scope", ["all", "namespace"], "namespace", True),
            q_text("virt_namespace", "Virt Namespace", "virt-demo", False),
        ],
    },
    "OCP Virt Demo - VM Instance Status": {
        "name": "VM Instance Survey",
        "description": "Scope running VM instance reporting.",
        "spec": [
            q_choice("virt_scope", "Inventory Scope", ["all", "namespace"], "namespace", True),
            q_text("virt_namespace", "Virt Namespace", "virt-demo", False),
        ],
    },
    "OCP Virt Demo - Storage Inventory": {
        "name": "Virt Storage Survey",
        "description": "Scope storage inventory reporting.",
        "spec": [
            q_choice("virt_scope", "Inventory Scope", ["all", "namespace"], "namespace", True),
            q_text("virt_namespace", "Virt Namespace", "virt-demo", False),
        ],
    },
    "OCP Virt Demo - VM Templates": {
        "name": "VM Templates Survey",
        "description": "Template and instance type reporting options.",
        "spec": [
            q_text(
                "template_namespace",
                "Template Namespace",
                "openshift",
                False,
                "Namespace used when listing VM templates.",
            ),
        ],
    },
    "OCP Admin - Ensure Demo Project": {
        "name": "Demo Project Survey",
        "description": "Configure the OpenShift demo project.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
        ],
    },
    "OCP Admin - Deploy Sample Application": {
        "name": "Deploy Application Survey",
        "description": "Configure the sample application deployment.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text("demo_app_name", "Application Name", "aap-demo-app", True),
            q_text(
                "demo_image",
                "Container Image",
                "quay.io/nginx/nginx-unprivileged:stable",
                True,
            ),
            q_integer("demo_replicas", "Replica Count", 2, True),
        ],
    },
    "OCP Admin - Expose Service Route": {
        "name": "Expose Route Survey",
        "description": "Configure the public OpenShift Route.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text("demo_route_name", "Route Name", "aap-demo", True),
            q_text("demo_app_name", "Service Name", "aap-demo-app", True),
        ],
    },
    "OCP Admin - Apply Network Policy": {
        "name": "Network Policy Survey",
        "description": "Configure namespace network policy.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text(
                "network_policy_name",
                "NetworkPolicy Name",
                "aap-demo-allow-same-namespace",
                True,
            ),
        ],
    },
    "OCP Admin - Configure Resource Quota": {
        "name": "Resource Quota Survey",
        "description": "Configure namespace quotas and limits.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text("resource_quota_pods", "Max Pods", "10", True),
            q_text("resource_quota_requests_cpu", "CPU Request Quota", "2", True),
            q_text("resource_quota_requests_memory", "Memory Request Quota", "4Gi", True),
        ],
    },
    "OCP Admin - Create Service Account RBAC": {
        "name": "RBAC Survey",
        "description": "Configure demo service account and role.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text("sa_name", "ServiceAccount Name", "aap-demo-automation", True),
            q_text("role_name", "Role Name", "aap-demo-viewer", True),
        ],
    },
    "OCP Admin - Scale Application": {
        "name": "Scale Application Survey",
        "description": "Scale the demo application deployment.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text("demo_app_name", "Application Name", "aap-demo-app", True),
            q_integer("demo_replicas", "Replica Count", 3, True),
        ],
    },
    "OCP Admin - Check Cluster Updates": {
        "name": "Cluster Updates Survey",
        "description": "Cluster update reporting options.",
        "spec": [
            q_choice(
                "show_available_updates",
                "List Available Updates",
                ["yes", "no"],
                "yes",
                True,
            ),
        ],
    },
    "OCP Admin - Install Cluster Operator": {
        "name": "Install Operator Survey",
        "description": "Install an operator from OperatorHub.",
        "spec": [
            q_text("operator_install_namespace", "Operator Namespace", "openshift-nmstate", True),
            q_text("operator_package", "Operator Package", "kubernetes-nmstate-operator", True),
            q_text("operator_channel", "Operator Channel", "stable", True),
            q_text("operator_source", "Catalog Source", "redhat-operators", True),
            q_text("operator_source_namespace", "Catalog Namespace", "openshift-marketplace", True),
        ],
    },
    "OCP Admin - Manage Route Networking": {
        "name": "Route Networking Survey",
        "description": "Tune route networking and TLS behavior.",
        "spec": [
            q_text("demo_namespace", "Demo Namespace", "aap-demo", True),
            q_text("demo_route_name", "Route Name", "aap-demo", True),
            q_text("route_timeout", "Route Timeout", "30s", True),
            q_text("route_balance", "Load Balance Algorithm", "roundrobin", True),
        ],
    },
    "CNV Admin - Ensure Virt Namespace": {
        "name": "Virt Namespace Survey",
        "description": "Configure the virtualization demo namespace.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
        ],
    },
    "CNV Admin - Create Virtual Machine": {
        "name": "Create VM Survey",
        "description": "Configure a new virtual machine.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name", "aap-managed-cirros", True),
            q_text("virt_vm_memory", "Memory Request", "512Mi", True),
            q_integer("virt_vm_cpu", "CPU Cores", 1, True),
            q_text(
                "virt_container_image",
                "Container Disk Image",
                "quay.io/kubevirt/cirros-container-disk-demo",
                True,
            ),
        ],
    },
    "CNV Admin - Start Virtual Machine": {
        "name": "Start VM Survey",
        "description": "Select the VM to start.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name", "aap-managed-cirros", True),
        ],
    },
    "CNV Admin - Stop Virtual Machine": {
        "name": "Stop VM Survey",
        "description": "Select the VM to stop.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name", "aap-managed-cirros", True),
        ],
    },
    "CNV Admin - Restart Virtual Machine": {
        "name": "Restart VM Survey",
        "description": "Select the VM to restart.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name", "aap-managed-cirros", True),
        ],
    },
    "CNV Admin - Patch VM Resources": {
        "name": "Patch VM Survey",
        "description": "Resize VM CPU and memory.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name", "aap-managed-cirros", True),
            q_text("virt_vm_memory", "Memory Request", "1Gi", True),
            q_integer("virt_vm_cpu", "CPU Cores", 2, True),
        ],
    },
    "CNV Admin - Create Blank DataVolume": {
        "name": "DataVolume Survey",
        "description": "Create blank VM storage.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name Prefix", "aap-managed-cirros", True),
            q_text("datavolume_name", "DataVolume Name", "aap-managed-cirros-disk", True),
            q_text("datavolume_size", "Volume Size", "5Gi", True),
            q_text(
                "storage_class",
                "Storage Class",
                "ocs-external-storagecluster-ceph-rbd",
                True,
            ),
        ],
    },
    "CNV Admin - Delete Virtual Machine": {
        "name": "Delete VM Survey",
        "description": "Select the VM to delete.",
        "spec": [
            q_text("virt_namespace", "Virt Namespace", "virt-demo", True),
            q_text("virt_vm_name", "VM Name", "aap-managed-cirros", True),
            q_choice(
                "confirm_delete",
                "Confirm Delete",
                ["yes", "no"],
                "no",
                True,
                "Set to yes to delete the virtual machine.",
            ),
        ],
    },
}


def configure_surveys():
    templates = api(
        "GET",
        f"/api/controller/v2/job_templates/?organization={ORG_ID}&project={PROJECT_ID}&page_size=100",
    )
    configured = []
    for jt in templates.get("results", []):
        survey = SURVEYS.get(jt["name"])
        if not survey:
            continue
        api("POST", f"/api/controller/v2/job_templates/{jt['id']}/survey_spec/", survey)
        api("PATCH", f"/api/controller/v2/job_templates/{jt['id']}/", {"survey_enabled": True})
        configured.append(jt["name"])
        print(f"Configured survey for JT {jt['id']}: {jt['name']}")
    return configured


if __name__ == "__main__":
    names = configure_surveys()
    print(json.dumps({"survey_count": len(names), "job_templates": names}, indent=2))
