from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'', 'project.urls', name='main_site_urls'),
    host(r'mendel', 'project.mendels_profile_urls', name='mendels_profile'),
)