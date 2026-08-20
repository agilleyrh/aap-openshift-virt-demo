#!/usr/bin/env python3
"""Configure AAP resources for OpenShift / Virt demo."""
import json
import os
import time
import urllib.parse
import urllib.request
import ssl

AAP_URL = os.environ.get("AAP_CONTROLLER_URL", "https://aap-aap.apps.cluster-knmpg.dyn.redhatworkshops.io")
TOKEN = os.environ["AAP_MCP_TOKEN"]
OCP_HOST = "https://api.cluster-knmpg.dyn.redhatworkshops.io:6443"
OCP_TOKEN = os.environ["OCP_TOKEN"]
ORG_ID = 1
INVENTORY_ID = 1
EE_ID = 2
SCM_URL = "https://github.com/agilleyrh/aap-openshift-virt-demo.git"

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


def api_get(path):
    return api("GET", path)


def api_post(path, data):
    return api("POST", path, data)


def api_patch(path, data):
    return api("PATCH", path, data)


def find_or_create_credential():
    creds = api_get("/api/controller/v2/credentials/?organization=1&name=OpenShift%20knmpg%20Cluster")
    for c in creds.get("results", []):
        if c["name"] == "OpenShift knmpg Cluster":
            print(f"Using credential id={c['id']}")
            return c["id"]
    cred = api_post(
        "/api/controller/v2/credentials/",
        {
            "name": "OpenShift knmpg Cluster",
            "description": "Read-only/audit access to knmpg OpenShift cluster for demo playbooks",
            "organization": ORG_ID,
            "credential_type": 3,
            "inputs": {
                "host": OCP_HOST,
                "bearer_token": OCP_TOKEN,
                "verify_ssl": True,
            },
        },
    )
    print(f"Created credential id={cred['id']}")
    return cred["id"]


def find_or_create_project():
    projects = api_get("/api/controller/v2/projects/?organization=1&name=OpenShift%20and%20Virt%20Demo")
    for p in projects.get("results", []):
        if p["name"] == "OpenShift and Virt Demo":
            print(f"Using project id={p['id']}")
            return p["id"]
    project = api_post(
        "/api/controller/v2/projects/",
        {
            "name": "OpenShift and Virt Demo",
            "description": "Read-only playbooks for OpenShift and OpenShift Virtualization demos",
            "organization": ORG_ID,
            "scm_type": "git",
            "scm_url": SCM_URL,
            "scm_branch": "main",
            "scm_clean": True,
            "scm_delete_on_update": True,
            "scm_update_on_launch": True,
        },
    )
    print(f"Created project id={project['id']}")
    return project["id"]


def sync_project(project_id):
    update = api_post(f"/api/controller/v2/projects/{project_id}/update/", {})
    job_id = update["id"]
    print(f"Project sync job id={job_id}")
    for _ in range(60):
        job = api_get(f"/api/controller/v2/project_updates/{job_id}/")
        if job["status"] in ("successful", "failed", "error", "canceled"):
            print(f"Project sync status={job['status']}")
            if job["status"] != "successful":
                raise RuntimeError(f"Project sync failed: {job.get('job_explanation')}")
            return
        time.sleep(5)


def find_or_create_job_template(name, playbook, project_id, cred_id):
    jts = api_get(f"/api/controller/v2/job_templates/?organization={ORG_ID}&name={urllib.parse.quote(name)}")
    for jt in jts.get("results", []):
        if jt["name"] == name:
            api_patch(
                f"/api/controller/v2/job_templates/{jt['id']}/",
                {
                    "playbook": playbook,
                    "project": project_id,
                    "inventory": INVENTORY_ID,
                    "execution_environment": EE_ID,
                    "credentials": [cred_id],
                    "ask_variables_on_launch": False,
                    "diff_mode": False,
                },
            )
            print(f"Updated job template id={jt['id']} name={name}")
            return jt["id"]
    jt = api_post(
        "/api/controller/v2/job_templates/",
        {
            "name": name,
            "description": f"Read-only demo: {playbook}",
            "job_type": "run",
            "inventory": INVENTORY_ID,
            "project": project_id,
            "playbook": playbook,
            "execution_environment": EE_ID,
            "credentials": [cred_id],
            "organization": ORG_ID,
            "ask_variables_on_launch": False,
            "diff_mode": False,
        },
    )
    print(f"Created job template id={jt['id']} name={name}")
    return jt["id"]


def find_or_create_workflow(name, description, job_template_ids):
    import urllib.parse

    wjts = api_get(f"/api/controller/v2/workflow_job_templates/?organization={ORG_ID}&name={urllib.parse.quote(name)}")
    wjt_id = None
    for w in wjts.get("results", []):
        if w["name"] == name:
            wjt_id = w["id"]
            break
    if not wjt_id:
        wjt = api_post(
            "/api/controller/v2/workflow_job_templates/",
            {
                "name": name,
                "description": description,
                "organization": ORG_ID,
                "inventory": INVENTORY_ID,
                "ask_variables_on_launch": False,
            },
        )
        wjt_id = wjt["id"]
        print(f"Created workflow id={wjt_id} name={name}")
    else:
        print(f"Rebuilding workflow id={wjt_id} name={name}")
        nodes = api_get(f"/api/controller/v2/workflow_job_templates/{wjt_id}/workflow_nodes/")
        for node in nodes.get("results", []):
            api("DELETE", f"/api/controller/v2/workflow_job_template_nodes/{node['id']}/")

    node_ids = []
    for idx, jt_id in enumerate(job_template_ids):
        node = api_post(
            "/api/controller/v2/workflow_job_template_nodes/",
            {
                "identifier": f"node-{idx+1}",
                "workflow_job_template": wjt_id,
                "unified_job_template": jt_id,
            },
        )
        node_ids.append(node["id"])

    for i in range(len(node_ids) - 1):
        api_post(
            f"/api/controller/v2/workflow_job_template_nodes/{node_ids[i]}/success_nodes/",
            {"id": node_ids[i + 1]},
        )

    return wjt_id


if __name__ == "__main__":
    cred_id = find_or_create_credential()
    project_id = find_or_create_project()
    sync_project(project_id)

    openshift_jobs = [
        ("OCP Demo - Cluster Overview", "playbooks/openshift/01-cluster-overview.yml"),
        ("OCP Demo - Cluster Operators", "playbooks/openshift/02-cluster-operators.yml"),
        ("OCP Demo - Projects and Quotas", "playbooks/openshift/03-projects-and-quotas.yml"),
        ("OCP Demo - Workload Health", "playbooks/openshift/04-workload-health.yml"),
        ("OCP Demo - Routes and Ingress", "playbooks/openshift/05-routes-and-ingress.yml"),
    ]
    virt_jobs = [
        ("OCP Virt Demo - Install CNV", "playbooks/openshift-virt/00-install-cnv.yml"),
        ("OCP Virt Demo - CNV Operator Status", "playbooks/openshift-virt/01-cnv-operator-status.yml"),
        ("OCP Virt Demo - VM Inventory", "playbooks/openshift-virt/02-virtual-machines-inventory.yml"),
        ("OCP Virt Demo - VM Instance Status", "playbooks/openshift-virt/03-vm-instances-status.yml"),
        ("OCP Virt Demo - Storage Inventory", "playbooks/openshift-virt/04-storage-and-datavolumes.yml"),
        ("OCP Virt Demo - VM Templates", "playbooks/openshift-virt/05-vm-templates-inventory.yml"),
    ]

    ocp_jt_ids = []
    for name, pb in openshift_jobs:
        ocp_jt_ids.append(find_or_create_job_template(name, pb, project_id, cred_id))

    virt_jt_ids = []
    for name, pb in virt_jobs:
        virt_jt_ids.append(find_or_create_job_template(name, pb, project_id, cred_id))

    wf_platform = find_or_create_workflow(
        "WF - OpenShift Platform Audit",
        "Read-only audit of OpenShift cluster health, projects, workloads, and routes.",
        ocp_jt_ids,
    )
    wf_virt = find_or_create_workflow(
        "WF - OpenShift Virtualization Audit",
        "Read-only audit of CNV operator status, VMs, storage, and templates.",
        virt_jt_ids[1:],
    )
    wf_virt_bootstrap = find_or_create_workflow(
        "WF - OpenShift Virtualization Bootstrap and Audit",
        "Install CNV if needed, then run the read-only virtualization audit playbooks.",
        virt_jt_ids,
    )
    wf_full = find_or_create_workflow(
        "WF - Full OpenShift and Virt Demo",
        "Complete demo workflow: OpenShift platform audit followed by virtualization bootstrap and audit.",
        ocp_jt_ids + virt_jt_ids,
    )

    print(json.dumps({
        "credential_id": cred_id,
        "project_id": project_id,
        "workflows": [wf_platform, wf_virt, wf_virt_bootstrap, wf_full],
    }, indent=2))
