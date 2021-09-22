from tenant_schemas.middleware import BaseTenantMiddleware,DefaultTenantMiddleware
from tenant_schemas.utils import get_public_schema_name
import logging

logger = logging.getLogger(__name__)
class WorkspaceMiddleware(BaseTenantMiddleware):
    def get_tenant(self, model, hostname, request):
        # return super().get_tenant(model, hostname, request)
        if request.user.is_authenticated and request.user.workspace:
            tenant =  request.user.workspace
        else:
            tenant =  model.objects.get(schema_name = get_public_schema_name())
        logger.warning(tenant.schema_name)
        
        return tenant
