import sys
from pathlib import Path
import json

import lxml.etree
import requests
import time

from runner import vars

#webpagetest.org rest api documentation at https://sites.google.com/a/webpagetest.org/docs/advanced-features/webpagetest-restful-apis
#Google insights api documentation at https://developers.google.com/speed/docs/insights/v1/reference

RUNS_PER_TEST = 4

def loading_dots():
    while True:
        yield("\r.  ")
        yield("\r.. ")
        yield("\r...")

def run(domain, save_file_loc=None, insight_sav_loc=None):

    csv, first_load, repeat_load = pagespeed(domain)
    if save_file_loc:
        save_file_loc = Path(save_file_loc)
        save_file_loc.write_bytes(csv)

    print()
    print("First view load time: ", first_load, " seconds")
    print("Repeat view load time: ", repeat_load, " seconds")

    result, rating = google_insights(domain)
    if insight_sav_loc:
        insight_sav_loc = Path(insight_sav_loc)

        csv = ""
        for key in result.keys():
            csv += key + ","
        csv.rstrip(",")
        csv += "\n"
        for val in result.values():
            csv += val + ","

        insight_sav_loc.write_bytes(csv)

    print("Google insight score: ", rating, "/100")

def google_insights(domain):
    """ performs a google insights test, and returns the results """
    s = requests.session()
    params = {
        "url": "http://" + domain,
        "key": vars.google_drive_client_secret
    }
    res = s.get("https://www.googleapis.com/pagespeedonline/v2/runPagespeed", params=params).text
    #import pprint; pprint.pprint(json.loads(res))

    data = json.loads(res)
    title = data["title"]
    score = data["ruleGroups"]["SPEED"].get("score")
    pageStats = data["pageStats"] #breaks down js, css, etc. by bytes and number of requests

    cssResponseBytes = int(pageStats.get("cssResponseBytes", 0))
    htmlResponseBytes = int(pageStats.get("htmlResponseBytes", 0))
    imageResponseBytes = int(pageStats.get("imageResponseBytes", 0))
    javascriptResponseBytes = int(pageStats.get("javascriptResponseBytes", 0))
    otherResponseBytes = int(pageStats.get("otherResponseBytes", 0))
    totalRequestBytes = int(pageStats.get("totalRequestBytes", 0))

    totalResponseBytes = cssResponseBytes + htmlResponseBytes + imageResponseBytes + javascriptResponseBytes + otherResponseBytes
    cssBytesReceived = round(cssResponseBytes / totalResponseBytes * 100, 2)
    htmlBytesReceived = round(htmlResponseBytes / totalResponseBytes * 100, 2)
    imageBytesReceived = round(imageResponseBytes / totalResponseBytes * 100, 2)
    jsBytesReceived = round(javascriptResponseBytes / totalResponseBytes * 100, 2)
    otherBytesReceived = round(otherResponseBytes / totalResponseBytes * 100, 2)

    numberResources = pageStats.get("numberResources")

    results = data["formattedResults"]["ruleResults"]
    PrioritizeVisibleContent = round(results["PrioritizeVisibleContent"].get("ruleImpact", 0))
    EnableGzipCompression = round(results["EnableGzipCompression"].get("ruleImpact", 0))
    MinifyHTML = round(results["MinifyHTML"].get("ruleImpact", 0))
    MinifyCss = round(results["MinifyCss"].get("ruleImpact", 0))
    AvoidLandingPageRedirects = round(results["AvoidLandingPageRedirects"].get("ruleImpact", 0))
    MinifyJavaScript = round(results["MinifyJavaScript"].get("ruleImpact", 0))
    LeverageBrowserCaching = round(results["LeverageBrowserCaching"].get("ruleImpact", 0))
    MinimizeRenderBlockingResources = round(results["MinimizeRenderBlockingResources"].get("ruleImpact", 0))
    MainResourceServerResponseTime = round(results["MainResourceServerResponseTime"].get("ruleImpact", 0))

    d = {
        "title": title.encode('ascii', errors='ignore'),
        "requests_made": numberResources,

        "total_bytes_Received": totalResponseBytes,
        "html_percentage": htmlBytesReceived,
        "css_percentage": cssBytesReceived,
        "js_percentage": jsBytesReceived,
        "image_percentage": imageBytesReceived,
        "other_percentage": otherBytesReceived,

        "prioritize_visible_content_impact": PrioritizeVisibleContent,
        "gzip_compression_impact": EnableGzipCompression,
        "minify_html_impact": MinifyHTML,
        "minify_css_impact": MinifyCss,
        "avoid_landing_page_redirects_impact": AvoidLandingPageRedirects,
        "minify_js_impact": MinifyJavaScript,
        "caching_impact": LeverageBrowserCaching,
        "render_blocking_resources_impact": MinimizeRenderBlockingResources,
        "server_response_time_impact": MainResourceServerResponseTime,

        "score": score
    }

    if vars.verbose:
        print("Here are the results of the Google Insights test: ")
        import pprint
        pprint.pprint(d)

    return (d, score)

def pagespeed(domain):
    """ Performs webpagetest.org tests, and returns the results """
    api_key = "A.d01883a3916a31ca52ac7cf481756263" #we're limited to 100 tests per day with this key
    resp = requests.post("http://www.webpagetest.org/runtest.php", params={
        "label": domain,
        "r": domain, # a request identifier
        "url": "http://"+domain,
        "k": api_key,
        "location": "ec2-us-west-2:Chrome.FIOS", #FIOS is 20 Mbps but this is not guaranteed to be consistant
        "f": "xml",
        "runs": RUNS_PER_TEST,
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
    max_attempts = 100
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

    fv_load_time = str(lxml.etree.tostring(fv_load_time))[12:-14]
    fv_load_time = int(fv_load_time)/1000
    rv_load_time = str(lxml.etree.tostring(rv_load_time))[12:-14]
    rv_load_time = int(rv_load_time)/1000

    resp = requests.get(csv_summary_url)

    return (resp.content, fv_load_time, rv_load_time)


# A sample Google Insights response can be found at https://developers.google.com/speed/docs/insights/v1/reference#alttypes_pagespeedonline_pagespeedapi_runpagespeed_json
# Below is a sample of the pagespeed data for the first view data
"""
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
