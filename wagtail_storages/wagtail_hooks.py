import django

import wagtail

from wagtail_storages import backends, utils

HOOK_ORDER = getattr(
    django.conf.settings,
    'WAGTAIL_STORAGES_DOCUMENT_HOOK_ORDER',
    100
)


@wagtail.core.hooks.register('before_serve_document', order=HOOK_ORDER)
def serve_document_from_s3(document, request):
    # Skip this hook if not using django-storages boto3 backend.
    if not utils.is_s3_boto3_storage_used():
        return

    # Send document_served signal.
    wagtail.documents.models.document_served.send(
        sender=wagtail.documents.models.get_document_model(),
        instance=document,
        request=request
    )

    # If document has restrictions, generate a signed URL, otherwise
    # return its public URL.
    if document.collection.get_view_restrictions():
        backend = backends.S3Boto3StorageForWagtailDocument()
        file_url = backend.url(document.file.name)
    else:
        file_url = document.file.url

    # Generate redirect response and add never_cache headers.
    response = django.shortcuts.redirect(file_url)
    del response['Cache-control']
    django.utils.cache.add_never_cache_headers(response)
    return response
