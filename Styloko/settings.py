# Scrapy settings for Styloko project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'Styloko'

SPIDER_MODULES = ['Styloko.spiders']
NEWSPIDER_MODULE = 'Styloko.spiders'
TEMPLATES_DIR = 'templates/'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'Styloko (+http://www.yourdomain.com)'
