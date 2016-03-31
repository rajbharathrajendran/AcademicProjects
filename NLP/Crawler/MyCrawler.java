import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.Set;
import java.util.regex.Pattern;

import edu.uci.ics.crawler4j.crawler.Page;
import edu.uci.ics.crawler4j.crawler.WebCrawler;
import edu.uci.ics.crawler4j.parser.HtmlParseData;
import edu.uci.ics.crawler4j.url.WebURL;


public class MyCrawler extends WebCrawler {
	String crawlStorageFolder = "C://data/crawl/history/";
	
	@Override
	public boolean shouldVisit(Page refferringPage,WebURL url) {
		String href = url.getURL().toLowerCase();
		boolean shouldVisit = (href.startsWith("https://ta.wikipedia.org/wiki/") || href.startsWith("http://ta.wikipedia.org/wiki/")); //&& !FILTERS.matcher(href).matches();
		return shouldVisit;
	}

	@Override
	public void visit(Page page) {
		String url = page.getWebURL().getURL();
		System.out.println("URL: " + url);
		if (page.getParseData() instanceof HtmlParseData) {
			HtmlParseData htmlParseData = (HtmlParseData) page.getParseData();
			String text = htmlParseData.getText();
			String html = htmlParseData.getHtml();
			int begin = html.indexOf("<title>");
			int end = html.indexOf("</title>");
			Set<WebURL> links = htmlParseData.getOutgoingUrls();
			System.out.println("Text length: " + text.length());
			System.out.println("Html length: " + html.length());
			System.out.println("Number of outgoing links: " + links.size());
			try {

				Writer out = new BufferedWriter(new OutputStreamWriter(
						new FileOutputStream(crawlStorageFolder+html.substring(begin + 8, end)+".txt"), "UTF8"));

				out.append(text);

				out.flush();
				out.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}
}
