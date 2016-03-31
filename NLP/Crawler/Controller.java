import edu.uci.ics.crawler4j.crawler.CrawlConfig;
import edu.uci.ics.crawler4j.crawler.CrawlController;
import edu.uci.ics.crawler4j.fetcher.PageFetcher;
import edu.uci.ics.crawler4j.robotstxt.RobotstxtConfig;
import edu.uci.ics.crawler4j.robotstxt.RobotstxtServer;


public class Controller {
	public static void main(String[] args) throws Exception {
		String crawlStorageFolder = "C://data/crawl/";
		int numberOfCrawlers = 7;
		CrawlConfig config = new CrawlConfig();
		config.setCrawlStorageFolder(crawlStorageFolder);
		config.setMaxDepthOfCrawling(5);
		config.setMaxPagesToFetch(500);
		config.setIncludeBinaryContentInCrawling(true);
		config.setMaxDownloadSize(Integer.MAX_VALUE);
		config.setPolitenessDelay(300);
		PageFetcher pageFetcher = new PageFetcher(config);
		RobotstxtConfig robotstxtConfig = new RobotstxtConfig();
		RobotstxtServer robotstxtServer = new RobotstxtServer(robotstxtConfig, pageFetcher);
		CrawlController controller = new CrawlController(config, pageFetcher, robotstxtServer);
		
		controller.addSeed("https://ta.wikipedia.org/wiki/%E0%AE%AA%E0%AE%95%E0%AF%81%E0%AE%AA%E0%AF%8D%E0%AE%AA%E0%AF%81:%E0%AE%87%E0%AE%A8%E0%AF%8D%E0%AE%A4%E0%AE%BF%E0%AE%AF_%E0%AE%B5%E0%AE%B0%E0%AE%B2%E0%AE%BE%E0%AE%B1%E0%AF%81");
		
		controller.start(MyCrawler.class, numberOfCrawlers);

		controller.shutdown();
	}
}
