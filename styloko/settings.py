# scrapy settings for styloko project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'styloko'

SPIDER_MODULES = ['styloko.spiders']
NEWSPIDER_MODULE = 'styloko.spiders'
TEMPLATES_DIR = 'templates/'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#UsER_AGENT = 'styloko (+http://www.yourdomain.com)'
