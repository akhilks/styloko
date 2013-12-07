import urlparse

# makes URLs absolute based on the context's response's URL
def absolute_url(iter_url, loader_context):
    response = loader_context.get('response')
    if not response:
        raise RuntimeError("no response in Item Loader context")
    for url in iter_url:
        yield urlparse.urljoin(response.url, url)

def absolute_url_value(url, loader_context):
    response = loader_context.get('response')
    if not response:
        raise RuntimeError("no response in Item Loader context")
    return urlparse.urljoin(response.url, url)
