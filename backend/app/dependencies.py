import uuid

from fastapi import Request


def get_tenant_id(request: Request) -> uuid.UUID:
    return request.state.tenant_id
