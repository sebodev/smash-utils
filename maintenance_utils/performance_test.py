import sys
from pathlib import Path

import lxml.etree
import requests
import time

from runner import vars

#webpagetest.org rest api documentation at https://sites.google.com/a/webpagetest.org/docs/advanced-features/webpagetest-restful-apis

def main(domain, save_file_loc=None):
    return run(domain, save_file_loc)

def loading_dots():
    while True:
        yield("\r.  ")
        yield("\r.. ")
        yield("\r...")

def run(domain, save_file_loc=None):
    api_key = "A.d01883a3916a31ca52ac7cf481756263" #we're limited to 100 tests per day with this key
    resp = requests.post("http://www.webpagetest.org/runtest.php", params={
        "label": domain,
        "r": domain, # a request identifier
        "url": "http://"+domain,
        "k": api_key,
        "location": "ec2-us-west-2:Chrome.FIOS", #FIOS is 20 Mbps but this is not guaranteed to be consistant
        "f": "xml"
    })
    root = lxml.etree.fromstring(resp.content)
    xml_url = root.xpath(".//xmlUrl/child::text()")[0]
    csv_summary_url = root.xpath(".//summaryCSV/child::text()")[0]
    csv_details_url = root.xpath(".//detailCSV/child::text()")[0]

    if vars.verbose:
        print("waiting for XML to appear at", xml_url)
        print("waiting for CSV to appear at", csv_url)

    def is_test_finished():
        resp = requests.get(xml_url)
        root = lxml.etree.fromstring(resp.content)
        status = root.xpath(".//statusCode/child::text()")[0]
        if "100" in status or "101" in status:
            return False
        return True

    time.sleep(2)
    max_attempts = 50
    dots = loading_dots()
    for i in range(max_attempts):
        if is_test_finished():
            break

        time.sleep(3)
        print(next(dots), end="", flush=True)
        sys.stdout.flush()
        time.sleep(3)
        print(next(dots), end="", flush=True)
        sys.stdout.flush()
    else:
        raise Exception("timed out")



    resp = requests.get(xml_url) #add params={"pagespeed": "1"} to get scorecard results
    root = lxml.etree.fromstring(resp.content)
    fv = first_view = root.find(".//data/run/firstView/results")
    rv = repeat_view = root.find(".//data/run/repeatView/results")

    fv_load_time = fv.find(".//loadTime")
    rv_load_time = rv.find(".//loadTime")
    print()
    fv_load_time = str(lxml.etree.tostring(fv_load_time))[12:-14]
    fv_load_time = int(fv_load_time)/1000
    rv_load_time = str(lxml.etree.tostring(rv_load_time))[12:-14]
    rv_load_time = int(rv_load_time)/1000
    print("first view load time:", fv_load_time, " seconds")
    print("repeat view load time: ", rv_load_time, " seconds")

    if save_file_loc:
        resp = requests.get(csv_summary_url)
        save_file_loc = Path(save_file_loc)
        save_file_loc.write_bytes(resp.content)


"""
Below is a sample first view data result
<URL>http://unifiedfireservicearea.com</URL>
<loadTime>3715</loadTime>
<TTFB>520</TTFB>
<bytesOut>15227</bytesOut>
<bytesOutDoc>14836</bytesOutDoc>
<bytesIn>879799</bytesIn>
<bytesInDoc>875329</bytesInDoc>
<connections>10</connections>
<requests>32</requests>
<requestsFull>32</requestsFull>
<requestsDoc>31</requestsDoc>
<responses_200>31</responses_200>
<responses_404>1</responses_404>
<responses_other>0</responses_other>
<result>99999</result>
<render>3475</render>
<fullyLoaded>4096</fullyLoaded>
<cached>0</cached>
<docTime>3715</docTime>
<domTime>0</domTime>
<score_cache>8</score_cache>
<score_cdn>10</score_cdn>
<score_gzip>100</score_gzip>
<score_cookies>-1</score_cookies>
<score_keep-alive>100</score_keep-alive>
<score_minify>-1</score_minify>
<score_combine>100</score_combine>
<score_compress>81</score_compress>
<score_etags>-1</score_etags>
<gzip_total>266196</gzip_total>
<gzip_savings>0</gzip_savings>
<minify_total>0</minify_total>
<minify_savings>0</minify_savings>
<image_total>579651</image_total>
<image_savings>106150</image_savings>
<base_page_redirects>0</base_page_redirects>
<optimization_checked>1</optimization_checked>
<aft>0</aft>
<domElements>193</domElements>
<pageSpeedVersion>1.9</pageSpeedVersion>
<title>Unified Fire Service Area</title>
<titleTime>973</titleTime>
<loadEventStart>3600</loadEventStart>
<loadEventEnd>3613</loadEventEnd>
<domContentLoadedEventStart>2606</domContentLoadedEventStart>
<domContentLoadedEventEnd>2717</domContentLoadedEventEnd>
<lastVisualChange>4474</lastVisualChange>
<browser_name>Google Chrome</browser_name>
<browser_version>53.0.2785.116</browser_version>
<server_count>1</server_count>
<server_rtt>56</server_rtt>
<base_page_cdn/>
<adult_site>0</adult_site>
<eventName>Step 1</eventName>
<fixed_viewport>1</fixed_viewport>
<score_progressive_jpeg>0</score_progressive_jpeg>
<firstPaint>3159</firstPaint>
<docCPUms>3260.421</docCPUms>
<fullyLoadedCPUms>3744.024</fullyLoadedCPUms>
<docCPUpct>87</docCPUpct>
<fullyLoadedCPUpct>60</fullyLoadedCPUpct>
<isResponsive>-1</isResponsive>
<browser_process_count>8</browser_process_count>
<browser_main_memory_kb>57516</browser_main_memory_kb>
<browser_other_private_memory_kb>67176</browser_other_private_memory_kb>
<browser_working_set_kb>124692</browser_working_set_kb>
<domInteractive>2606</domInteractive>
<domLoading>0</domLoading>
<base_page_ttfb>520</base_page_ttfb>
<date>1474521500</date>
<SpeedIndex>3717</SpeedIndex>
<visualComplete>4474</visualComplete>
<run>1</run>
<step>1</step>
<effectiveBps>246028</effectiveBps>
<effectiveBpsDoc>273968</effectiveBpsDoc>
"""
