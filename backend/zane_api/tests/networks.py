# type: ignore
from .base import AuthAPITestCase
from django.urls import reverse
from ..models import (
    Deployment,
    DeploymentChange,
    HealthCheck,
)
from rest_framework import status
import responses
import re
from django.conf import settings
from temporal.activities import get_swarm_service_name_for_deployment
from temporal.schedules import MonitorDockerDeploymentWorkflow
from temporal.shared import (
    HealthcheckDeploymentDetails,
    SimpleDeploymentDetails,
    HealthCheckDto,
)


class DockerServiceNetworksTests(AuthAPITestCase):
    async def test_service_added_to_global_network(self):
        p, service = await self.acreate_and_deploy_redis_docker_service()

        deployment: Deployment = await service.deployments.afirst()
        service = self.fake_docker_client.get_deployment_service(deployment=deployment)
        service_networks = {net["Target"]: net["Aliases"] for net in service.networks}
        self.assertTrue("zane" in service_networks)

    @responses.activate
    async def test_healthcheck_path_uses_container_id_to_run_healthcheck(
        self,
    ):
        responses.add_passthru(settings.CADDY_PROXY_ADMIN_HOST)
        responses.add_passthru(settings.LOKI_HOST)

        p, service = await self.acreate_and_deploy_caddy_docker_service()
        deployment_url_pattern = re.compile(
            r"http:\/\/[a-z0-9]{12}:\d+/.*",
            re.IGNORECASE,
        )
        responses.add(
            responses.GET,
            url=deployment_url_pattern,
            status=status.HTTP_200_OK,
        )

        await DeploymentChange.objects.acreate(
            field=DeploymentChange.ChangeField.HEALTHCHECK,
            type=DeploymentChange.ChangeType.UPDATE,
            new_value={
                "type": "PATH",
                "value": "/",
                "timeout_seconds": 5,
                "interval_seconds": 30,
                "associated_port": 80,
            },
            old_value=None,
            service=service,
        )

        response = await self.async_client.put(
            reverse(
                "zane_api:services.docker.deploy_service",
                kwargs={
                    "project_slug": p.slug,
                    "env_slug": "production",
                    "service_slug": service.slug,
                },
            ),
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        latest_deployment: Deployment = await service.deployments.afirst()
        self.assertEqual(Deployment.DeploymentStatus.HEALTHY, latest_deployment.status)

    @responses.activate
    async def test_monitor_healthcheck_path_uses_container_id_to_run_healthcheck(
        self,
    ):
        responses.add_passthru(settings.CADDY_PROXY_ADMIN_HOST)
        responses.add_passthru(settings.LOKI_HOST)
        p, service = await self.acreate_and_deploy_caddy_docker_service()
        deployment_url_pattern = re.compile(
            r"http:\/\/[a-z0-9]{12}:\d+/.*", re.IGNORECASE
        )
        responses.add(
            responses.GET,
            url=deployment_url_pattern,
            status=status.HTTP_200_OK,
        )

        await DeploymentChange.objects.acreate(
            field=DeploymentChange.ChangeField.HEALTHCHECK,
            type=DeploymentChange.ChangeType.UPDATE,
            new_value={
                "type": "PATH",
                "value": "/",
                "timeout_seconds": 30,
                "interval_seconds": 30,
                "associated_port": 80,
            },
            service=service,
        )

        response = await self.async_client.put(
            reverse(
                "zane_api:services.docker.deploy_service",
                kwargs={
                    "project_slug": p.slug,
                    "env_slug": "production",
                    "service_slug": service.slug,
                },
            ),
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        latest_deployment = await service.deployments.afirst()
        self.assertEqual(Deployment.DeploymentStatus.HEALTHY, latest_deployment.status)

        # Run monitor healthcheck manually
        latest_deployment = await service.alatest_production_deployment
        self.assertEqual(Deployment.DeploymentStatus.HEALTHY, latest_deployment.status)

        async with self.workflowEnvironment() as env:  # type: WorkflowEnvironment
            healthcheck: HealthCheck | None = latest_deployment.service.healthcheck
            healthcheck_details = HealthcheckDeploymentDetails(
                deployment=SimpleDeploymentDetails(
                    hash=latest_deployment.hash,
                    service_id=latest_deployment.service.id,
                    project_id=latest_deployment.service.project_id,
                    urls=[url.domain async for url in latest_deployment.urls.all()],
                ),
                healthcheck=(
                    HealthCheckDto.from_dict(
                        dict(
                            type=healthcheck.type,
                            value=healthcheck.value,
                            timeout_seconds=healthcheck.timeout_seconds,
                            interval_seconds=healthcheck.interval_seconds,
                            id=healthcheck.id,
                            associated_port=healthcheck.associated_port,
                        )
                    )
                    if healthcheck is not None
                    else None
                ),
            )
            await env.client.execute_workflow(
                workflow=MonitorDockerDeploymentWorkflow.run,
                arg=healthcheck_details,
                id=latest_deployment.monitor_schedule_id,
                task_queue=settings.TEMPORALIO_MAIN_TASK_QUEUE,
                execution_timeout=settings.TEMPORALIO_WORKFLOW_EXECUTION_MAX_TIMEOUT,
            )

            self.assertEqual(
                Deployment.DeploymentStatus.HEALTHY, latest_deployment.status
            )
