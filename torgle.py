#!/usr/bin/python

import urllib
import time
import re
import MySQLdb

def onion_dl(onion):
    try:
        return urllib.urlopen('http://' + onion).read()
    except:
        return ''

def newest_site():
    cur.execute("SELECT url FROM search_sites ORDER BY last_checked ASC LIMIT 1") 
    return cur.fetchone()[0]

def add_links(site, links):
    site_base_url = site.split(".onion")[0]

    for link in links:
        if site_base_url != link.split('.onion'):
            cur.execute("SELECT linked_from FROM search_sites WHERE url='%s'" % link)
            all_results = cur.fetchall()
        
            if all_results:
                link_linked_from = all_results[0][0].split(",")
                link_linked_from.append(site)
                link_linked_from = ",".join(list(set(link_linked_from)))
                cur.execute("UPDATE search_sites SET linked_from='%s', link_count=%d WHERE url='%s'" % (link_linked_from, len(link_linked_from.split(',')), link))
            else:
                cur.execute("INSERT INTO search_sites (url, links_to, linked_from, last_checked, content, searchable, link_count) VALUES ('%s', '', '%s', 0, '', '', 1)" % (link, site))

con = MySQLdb.connect("hostname", "username", "password", "database")
cur = con.cursor()

html_regex = re.compile("<.*?>")
abs_link_regex = re.compile("\w+?\.onion?/[\w\.\/]*")
rel_link_regex = re.compile('(<\s*a[^>]+href\s*=\s*["\']?)(?!http)([^"\'>]+)', re.IGNORECASE)

while True:
    site = newest_site()
    second = int(time.time())


    html = con.escape_string(onion_dl(site).lower())
    clean = html_regex.sub('', html)
    absolute_links = abs_link_regex.findall(html)
    relative_links = [i[1] for i in rel_link_regex.findall(html.replace("\\", ""))]

    links = absolute_links

    for i in relative_links:
        if abs_link_regex.match(i) == None and i[0] != "#":
            if i[0] == '/':
                onion = site.split(".onion")[0] + '.onion'
                links.append(onion + i)
            else:
                if site[-1] == '/':
                    links.append(site + i)
                else:
                    links.append(site + '/' + i)

    links = list(set(links))

    if html:    
        cur.execute("UPDATE search_sites SET content='%s', searchable='%s', last_checked=%d, links_to='%s' WHERE url='%s'" % (html, clean, second, ",".join(links), site))
        add_links(site, links)
    else:
        cur.execute("UPDATE search_sites SET last_checked=%d WHERE url='%s'" % (second, site))