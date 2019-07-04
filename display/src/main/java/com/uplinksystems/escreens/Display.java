package com.uplinksystems.escreens;

import com.sun.jna.NativeLibrary;
import org.joda.time.DateTime;
import org.joda.time.LocalDateTime;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import uk.co.caprica.vlcj.binding.internal.libvlc_media_t;
import uk.co.caprica.vlcj.component.EmbeddedMediaPlayerComponent;
import uk.co.caprica.vlcj.medialist.MediaList;
import uk.co.caprica.vlcj.player.MediaPlayer;
import uk.co.caprica.vlcj.player.MediaPlayerEventListener;
import uk.co.caprica.vlcj.player.MediaPlayerFactory;
import uk.co.caprica.vlcj.player.embedded.EmbeddedMediaPlayer;
import uk.co.caprica.vlcj.player.embedded.videosurface.CanvasVideoSurface;
import uk.co.caprica.vlcj.player.list.MediaListPlayer;
import uk.co.caprica.vlcj.player.list.MediaListPlayerMode;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.Time;
import java.time.DayOfWeek;
import java.util.*;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class Display {

    private JSONObject json;
    private String name;
    private int width, height, rotation, version;
    private Font largeFont, mediumFont;
    private List<Event> events;
    private List<Default> defaults;
    private List<String> pings;
    private Map<String, Image> loadedImages;
    private Media fallback, currentMedia;
    private Map<String, Boolean> pingStatus;
    private DateTimeFormatter dateTimeFormatter, dateFormatter;
    private Image missingConfig;
    private boolean configured;
    private JFrame frame;
    private Panel currentPanel;
    private String hash;
    private boolean isProduction;
    private EmbeddedMediaPlayer mediaPlayer;
    private MediaPlayerFactory mediaPlayerFactory;
    private MediaListPlayer mediaListPlayer;

    // Constants
    private final String MEDIA_DIRECTORY = "media/";
    private final String CONFIG_FILE = "config.json";
    private final String SERVER_IP = "10.0.128.200";
    private final int SERVER_PORT = 5001;
    private final String SERVER_ADDRESS = "http://" + SERVER_IP + ":" + SERVER_PORT + "/";
    private final int CONFIG_UPDATE_INTERVAL = 10000;// 300000; // Every 5 minutes

    public static void main(String[] args) throws Exception {
        // Wait for display
        while (GraphicsEnvironment.isHeadless()) ;
        Thread.sleep(4000);
        Display display = new Display();
        SwingUtilities.invokeLater(display::createGUI);
        display.configuration();
    }

    private Display() throws Exception {
        NativeLibrary.addSearchPath("libvlc", "C:\\Program Files\\VideoLAN\\VLC");
        isProduction = "jar".equals(getClass().getResource("").getProtocol());
        hash = getMD5();
        System.out.println("Hash is: " + hash);
        largeFont = new Font("serif", Font.PLAIN, 128);
        mediumFont = new Font("serif", Font.PLAIN, 90);
        events = new ArrayList<>();
        defaults = new ArrayList<>();
        pingStatus = new HashMap<>();
        pings = new ArrayList<>();
        loadedImages = new HashMap<>();
        width = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration().getBounds().width;
        height = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration().getBounds().height;
        missingConfig = ImageIO.read(getClass().getResource("/missing_config.png"));
        dateTimeFormatter = DateTimeFormat.forPattern("MM/dd/yyyy HH:mm");
        dateFormatter = DateTimeFormat.forPattern("MM/dd/yyyy");
        String stringVersion = Display.class.getPackage().getSpecificationVersion();
        version = stringVersion == null ? 0 : Integer.valueOf(stringVersion);
        System.out.println("Version is: " + version);
        new Thread(this::updatePings).start();
        // Forced repaints
        new Thread(() -> {
            while (true) {
                if (frame != null)
                    SwingUtilities.invokeLater(() -> frame.repaint());
                try {
                    Thread.sleep(30000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }).start();
        //sendPutRequest("screen/screen1", "{\"language\":\"russian\", \"description\":\"yellow\"}");
        //sendGetRequest("screen/screen1");
        //sendPostRequest("media/test.zip", "test.zip");
    }

    // Gets the MD5 hash of the JAR
    private String getMD5() throws Exception {
        if (!isProduction)
            return "";
        String md5;
        try (InputStream is = Files.newInputStream(new File(Display.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toPath())) {
            md5 = org.apache.commons.codec.digest.DigestUtils.md5Hex(is);
            return md5;
        }
    }

    // Check if media changed and refresh display
    private void updateMedia() {
        while (true) {
            try {
                // Todo: handle media not available earlier so as to enable switching panels for videos and such not being present
                if (getCurrentMedia() != currentMedia && frame != null && frame.isVisible()) {
                    System.out.println("Invalidating");
                    currentMedia = getCurrentMedia();
                    switchMedia(currentMedia.type);
                    // Todo: Check if invalidation is necessary
                    //frame.invalidate();
                    SwingUtilities.invokeLater(() -> frame.repaint());
                    //frame.validate();
                }
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    private void rsync(String src, String dest) throws Exception {
        ProcessBuilder builder = new ProcessBuilder(Arrays.asList("rsync", "-e", "ssh -o StrictHostKeyChecking=no", "-avzh", "pi@" + SERVER_IP + ":" + src, dest));
        builder.redirectErrorStream(true);
        builder.redirectOutput(ProcessBuilder.Redirect.INHERIT);
        Process p = builder.start();
        p.waitFor(2, TimeUnit.MINUTES);
    }

    // Handle updating config file, media, and the program
    private void configuration() throws Exception {
        if (!new File(CONFIG_FILE).exists()) {
            System.out.println("Config File is missing!");
            return;
        }
        JSONParser parser = new JSONParser();
        try {
            json = (JSONObject) parser.parse(new FileReader(CONFIG_FILE));
        } catch (ParseException e) {
            System.out.println("Failed to parse config file, game over.");
            return;
        }
        parseJSON();
        configured = true;
        SwingUtilities.invokeLater(() -> frame.repaint());
        new Thread(this::updateMedia).start();
        while (true) {
            if (isProduction) {
                System.out.println("Updating JAR and media");
                rsync("/home/pi/escreens/media", "/home/pi/escreens");
                rsync("/home/pi/escreens/escreen.jar", "/home/pi/escreens");

                if (!hash.equals(getMD5())) {
                    System.out.println("New hash is: " + getMD5());
                    System.out.println("Restarting....");
                    System.exit(0);
                }
            }
            String response = "";
            int attempts = 0;
            while (attempts < 4 && "".equals(response)) {
                try {
                    response = sendGetRequest("screen/" + name + "?version=" + version);
                } catch (Exception e) {
                    System.out.println(e.getMessage());
                }
                if (!"".equals(response))
                    break;
                System.out.println("Attempt " + attempts + " to pull JSON file");
                attempts++;
                Thread.sleep(1000);
            }
            if (!"".equals(response)) {
                try {
                    JSONObject tempObject = (JSONObject) parser.parse(response);
                    if (!tempObject.equals(json)) {
                        json = tempObject;
                        parseJSON();
                        try (FileWriter file = new FileWriter(CONFIG_FILE)) {
                            file.write(json.toJSONString());
                            System.out.println("Updated JSON file");
                        }
                    } else {
                        System.out.println("JSON file was up to date");
                    }
                } catch (ParseException e) {
                    System.out.println("Couldn't parse received JSON file: " + response);
                }
            }
            Thread.sleep(CONFIG_UPDATE_INTERVAL);
        }
    }

    // Create thread to ping IPs in config
    private void updatePings() {
        while (true) {
            try {
                for (String ip : pings)
                    try {
                        pingStatus.put(ip, ping(ip));
                    } catch (Exception e) {
                        System.out.println(e);
                        pingStatus.put(ip, false);
                    }
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    private void parseJSON() {
        try {
            // Per display config
            JSONObject config = (JSONObject) json.get("config");
            name = (String) config.get("name");
            rotation = (int) (long) config.get("rotation");

            // In case of missing files or mid download
            this.fallback = mediaFromJSON((JSONObject) json.get("fallback"));

            // Default mode and file when no events are active
            JSONArray defaultArray = (JSONArray) json.get("defaults");
            for (Object object : defaultArray)
                defaults.add(defaultFromJSON((JSONObject) object));

            // Temporary changes from defaults when all conditions are met
            JSONArray eventArray = (JSONArray) json.get("events");
            for (Object object : eventArray)
                events.add(eventFromJSON((JSONObject) object));

            // Add any IPs to ping
            for (Default def : defaults)
                processMedia(def);
            for (Event event : events)
                processMedia(event);
            processMedia(fallback);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Check for IPs
    private void processMedia(Media media) {
        if (media.type == MediaType.MANUAL)
            for (Media manual : media.media.manualList)
                processMedia(manual);
        if ((media.type == MediaType.INSTAGRAM || media.type == MediaType.TWITCH || media.type == MediaType.YELP || media.type == MediaType.TWITTER) && !pings.contains(media.media.info))
            pings.add(media.media.info);
    }

    private List<Media> manualFromJSON(JSONArray array) {
        ArrayList<Media> manual = new ArrayList<>();
        for (Object object : array)
            manual.add(mediaFromJSON((JSONObject) object));
        return manual;
    }

    private MediaInfo mediaInfoFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        switch (type) {
            case MANUAL:
                return new MediaInfo(manualFromJSON((JSONArray) object.get("media")));
            case IMAGE:
                return new MediaInfo((String) object.get("media"));
            default:
                return new MediaInfo((String) object.get("media"));
        }
    }

    private Media mediaFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        return new Media(type, mediaInfoFromJSON(object));
    }

    private Default defaultFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        return new Default(type, mediaInfoFromJSON(object), dateTimeFormatter.parseDateTime((String) object.get("start_date_time")));
    }

    private Event eventFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        List<DayOfWeek> days = new ArrayList<>();
        JSONArray dayArray = (JSONArray) object.get("days");
        for (Object day : dayArray)
            days.add(DayOfWeek.valueOf((String) day));
        return new Event(type, mediaInfoFromJSON(object), dateTimeFormatter.parseDateTime((String) object.get("start_date_time")), dateTimeFormatter.parseDateTime((String) object.get("end_date_time")), timeFromString((String) object.get("start_time")), timeFromString((String) object.get("end_time")), days, (long) object.get("priority"));
    }

    private Time timeFromString(String time) {
        String[] split = time.split(":");
        return new Time(Integer.valueOf(split[0]), Integer.valueOf(split[1]), 0);
    }

    // Initialize all of the Swing components
    private void createGUI() {
        frame = new JFrame();
        frame.getContentPane().setLayout(new CardLayout());

        // Hide cursor
        BufferedImage cursorImg = new BufferedImage(16, 16, BufferedImage.TYPE_INT_ARGB);
        Cursor blankCursor = Toolkit.getDefaultToolkit().createCustomCursor(cursorImg, new Point(0, 0), "blank cursor");
        frame.getContentPane().setCursor(blankCursor);

        ArrayList<String> args = new ArrayList<>();
        if (rotation == 90 || rotation == 180) {
            args.add("--video-filter=rotate");
            args.add( "--rotate-angle=180");
        }
        mediaPlayerFactory = new MediaPlayerFactory(args);
        mediaListPlayer = mediaPlayerFactory.newMediaListPlayer();
        mediaPlayer = mediaPlayerFactory.newEmbeddedMediaPlayer();
        mediaListPlayer.setMediaPlayer(mediaPlayer);
        Canvas vlcCanvas = new Canvas();
        vlcCanvas.setBackground(Color.black);
        JPanel mediaPane = new JPanel();
        mediaPane.setLayout(new BorderLayout());
        mediaPane.add(vlcCanvas, BorderLayout.CENTER);
        mediaPlayer.setVideoSurface(mediaPlayerFactory.newVideoSurface(vlcCanvas));

        JPanel mainPane = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                draw(g);
            }
        };
        frame.add(Panel.MAIN.name(), mainPane);
        frame.add(Panel.MEDIA.name(), mediaPane);
        frame.setTitle("ZapDisplay");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setExtendedState(JFrame.MAXIMIZED_BOTH);
        frame.setUndecorated(true);
        frame.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                mediaPlayer.stop();
                mediaPlayerFactory.release();
                mediaPlayer.release();
                System.exit(0);
            }
        });
        frame.setResizable(true);
        frame.getGraphicsConfiguration().getDevice().setFullScreenWindow(frame);
        frame.setPreferredSize(frame.getGraphicsConfiguration().getBounds().getSize());
        switchPane(Panel.MAIN);
        frame.pack();
        frame.setVisible(true);
    }

    private void draw(Graphics g) {
        if (!configured) {
            g.setColor(Color.GREEN);
            g.fillRect(0, 0, width, height);
            g.setColor(Color.BLACK);
            g.setFont(largeFont);
            g.drawString("Loading...", 100, 200);
            return;
        }
        Graphics2D g2d = (Graphics2D) g;
        Media media = currentMedia;
        if (media == null) {
            System.out.println("The current media is null, abandon ship!");
            return;
        }
        if (!media.isAvailable()) {
            System.out.println("Media not isAvailable: " + media.media);
            media = fallback;
        }
        if (media == null)
            System.out.println("The fallback is null, abandon ship!");
        if (json == null || media == null) {
            g.setColor(Color.RED);
            g.setFont(largeFont);
            g.drawImage(missingConfig, 0, 0, width, height, null);
            g.drawString(json == null ? "Missing configuration file..." : "Media is null", width / 2, 200);
            return;
        }
        System.out.println("Drawing media: " + media);
        renderMedia(g2d, media);
    }

    private void switchMedia(MediaType media) {
        if (currentPanel == Panel.MEDIA) {
            mediaPlayer.stop();
            if (mediaListPlayer.getMediaList() != null)
                mediaListPlayer.getMediaList().release();
        }
        if (media == MediaType.VIDEO) {
            switchPane(Panel.MEDIA);
            mediaPlayer.playMedia(MEDIA_DIRECTORY + currentMedia.media.info);
            mediaPlayer.setRepeat(true);
        } else if (media == MediaType.SLIDESHOW) {
            switchPane(Panel.MEDIA);
            MediaList mediaList = mediaPlayerFactory.newMediaList();
            String[] splot = currentMedia.media.info.split(", ");
            for (int i = 1; i < splot.length; i++) {
                mediaList.addMedia(MEDIA_DIRECTORY + splot[i], splot[i].endsWith(".png") || splot[i].endsWith(".jpg") ? "image-duration=" + splot[0] : "stop-time=" + splot[0]);
            }
            mediaListPlayer.setMediaList(mediaList);
            mediaListPlayer.setMode(MediaListPlayerMode.LOOP);
            mediaListPlayer.play();
        } else
            switchPane(Panel.MAIN);
    }

    private void switchPane(Panel panel) {
        ((CardLayout) frame.getContentPane().getLayout()).show(frame.getContentPane(), panel.name());
        SwingUtilities.invokeLater(() -> frame.repaint());
        currentPanel = panel;
    }

    private void loadImage(String name) {
        String[] nameParts = name.split("\\.");
        String fileName = nameParts[0] + (((rotation / 90 % 2 == 0) ? "_horizontal." : "_vertical.") + nameParts[1]);
        if (!loadedImages.containsKey(fileName))
            try {
                loadedImages.put(name, rotateImage(ImageIO.read(new File(MEDIA_DIRECTORY + fileName))));
            } catch (Exception e) {
                e.printStackTrace();
            }
    }

    private void renderMedia(Graphics2D g, Media media) {
        switch (media.type) {
            case IMAGE:
                loadImage(media.media.info);
                g.drawImage(loadedImages.get(media.media.info), 0, 0, width, height, null);
                break;
            case YELP:

                break;
            case VIDEO:

                break;
            case MANUAL:

                break;
            case TWITCH:

                break;
            case TWITTER:

                break;
            case INSTAGRAM:

                break;
            case PRESENTATION:

                break;
            case SLIDESHOW:
                /*int duration = Integer.parseInt(media.media.info.substring(0, 1));
                int entries = (media.media.info.length() - media.media.info.replace(", ", "").length()) / 2;
                String current = media.media.info.split(", ")[((int) (System.currentTimeMillis() / 1000)) % (duration * entries) / duration + 1];
                loadImage(current);
                g.drawImage(loadedImages.get(current), 0, 0, width, height, null);*/
                break;
            case COUNTDOWN:
                String[] splot = media.media.info.split(", ");
                DateTime current = LocalDateTime.now().toDateTime();
                DateTime date0 = dateFormatter.parseDateTime(splot[2]);
                DateTime date1 = dateFormatter.parseDateTime(splot[4]);
                DateTime delta0 = date0.minus(current.getMillis());
                DateTime delta1 = date1.minus(current.getMillis());
                loadImage(splot[0]);
                g.drawImage(loadedImages.get(splot[0]), 0, 0, width, height, null);
                g.rotate(-Math.PI / 2, width / 2f, height / 2f);
                g.setFont(mediumFont);
                g.setColor(Color.BLACK);
                g.drawString(splot[1], 450, -100);
                g.drawString(splot[3], 480, 1000);
                g.setFont(largeFont);
                g.drawString(delta0 == date0 ? "00:00:00" : delta0.toString("dd:HH:mm"), 700, 100);
                g.drawString(delta1 == date1 ? "00:00:00" : delta1.toString("dd:HH:mm"), 700, 1200);
                g.rotate(Math.PI / 2, width / 2f, height / 2f);
                break;
        }
    }

    private Media getCurrentMedia() {
        for (Event event : events) {
            if (event.active())
                return event;
        }
        if (defaults.size() == 0)
            return fallback;
        Default earliest = defaults.get(0);
        for (Default def : defaults) {
            if (def.startDateTime.compareTo(LocalDateTime.now().toDateTime()) < 0 && def.startDateTime.compareTo(earliest.startDateTime) > 0)
                earliest = def;
        }
        return earliest;
    }

    private class MediaInfo {
        String info;
        List<Media> manualList;

        private MediaInfo(String info) {
            this.info = info;
        }

        private MediaInfo(List<Media> manualList) {
            this.manualList = manualList;
        }

        @Override
        public String toString() {
            return "Media(info=" + info + ", manualList=" + manualList + ")";
        }
    }

    private class Media {
        MediaType type;
        MediaInfo media;

        private Media(MediaType type, MediaInfo media) {
            this.type = type;
            this.media = media;
        }

        private boolean isAvailable() {
            if (type == MediaType.MANUAL) {
                for (Media manual : media.manualList)
                    if (manual.isAvailable())
                        return true;
                return true;
            } else if (type == MediaType.IMAGE) {
                return new File(MEDIA_DIRECTORY + insertImageOrientation(media.info)).exists();
            } else if (type == MediaType.SLIDESHOW) {
                // Todo: fix slideshow availibility, it don't work
                String[] entries = media.info.split(", ");
                for (int i = 1; i < entries.length; i++) {
                    if (!new File(MEDIA_DIRECTORY + entries[i]).exists())
                        return false;
                }
                return true;
            } else if (type == MediaType.PRESENTATION || type == MediaType.VIDEO)
                return new File(MEDIA_DIRECTORY + media.info).exists();
            else if (type == MediaType.COUNTDOWN)
                return new File(MEDIA_DIRECTORY + insertImageOrientation(media.info.split(", ")[0])).exists();
            else
                return pingStatus.get(media.info);

        }

        @Override
        public String toString() {
            return "Media(type=" + type.name() + ", media=" + media + ")";
        }
    }

    private class Default extends Media {
        DateTime startDateTime;

        public Default(MediaType type, MediaInfo media, DateTime startDateTime) {
            super(type, media);
            this.startDateTime = startDateTime;
        }

        @Override
        public String toString() {
            return "Default(type=" + type.name() + ", media=" + media + ", startDate=" + startDateTime + ")";
        }
    }

    private class Event extends Default {
        DateTime endDateTime;
        Time startTime, endTime;
        List<DayOfWeek> days;
        long priority;

        private Event(MediaType type, MediaInfo media, DateTime startDateTime, DateTime endDateTime, Time startTime, Time endTime, List<DayOfWeek> days, long priority) {
            super(type, media, startDateTime);
            this.endDateTime = endDateTime;
            this.startTime = startTime;
            this.endTime = endTime;
            this.days = days;
            this.priority = priority;
        }

        private boolean active() {
            // Todo: Finish
            return false;
        }

        @Override
        public String toString() {
            return "Event(type=" + type.name() + ", media=" + media + ", startDate=" + startDateTime + ", endDate=" + endDateTime + ", startTime=" + startTime + ", endTime=" + endTime + ", days=" + days + ", priority=" + priority + ")";
        }
    }

    private String insertImageOrientation(String imageName) {
        String[] nameParts = imageName.split("\\.");
        return nameParts[0] + ((rotation / 90 % 2 == 0) ? "_horizontal." : "_vertical.") + nameParts[1];
    }

    private enum Panel {
        MAIN, MEDIA
    }

    private enum MediaType {
        IMAGE, PRESENTATION, INSTAGRAM, MANUAL, TWITCH, YELP, VIDEO, TWITTER, SLIDESHOW, COUNTDOWN;

        private static MediaType fromString(String string) {
            return MediaType.valueOf(string.toUpperCase());
        }
    }

    private BufferedImage rotateImage(Image image) {
        double angle = Math.toRadians((rotation == 180 || rotation == 270) ? 180 : 0);
        double sin = Math.abs(Math.sin(angle)), cos = Math.abs(Math.cos(angle));
        int w = image.getWidth(null), h = image.getHeight(null);
        int neww = (int) Math.floor(w * cos + h * sin), newh = (int) Math.floor(h * cos + w * sin);
        GraphicsConfiguration gc = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration();
        BufferedImage result = gc.createCompatibleImage(neww, newh, Transparency.TRANSLUCENT);
        Graphics2D g = result.createGraphics();
        g.translate((neww - w) / 2, (newh - h) / 2);
        g.rotate(angle, w / 2.0, h / 2.0);
        g.drawImage(image, 0, 0, null);
        g.dispose();
        return result;
    }

    private boolean ping(String ipAddress) throws Exception {
        InetAddress geek = InetAddress.getByName(ipAddress);
        return geek.isReachable(5000);
    }

    private String sendGetRequest(String url) throws Exception {
        URL obj = new URL(SERVER_ADDRESS + url);
        HttpURLConnection con = (HttpURLConnection) obj.openConnection();
        con.setRequestMethod("GET");
        String encoding = Base64.getEncoder().encodeToString(("username:password").getBytes(StandardCharsets.UTF_8));
        con.setRequestProperty("AUTHORIZATION", "Basic " + encoding);
        con.setRequestProperty("Content-Type", "application/json");
        int responseCode = con.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            StringBuilder response = new StringBuilder();
            try (BufferedReader in = new BufferedReader(new InputStreamReader(con.getInputStream()))) {
                String inputLine;
                while ((inputLine = in.readLine()) != null)
                    response.append(inputLine);
            }
            return response.toString();
        } else {
            System.out.println("Get request failed: " + responseCode);
            return "";
        }
    }

    private String sendPutRequest(String url, String message) throws Exception {
        URL obj = new URL(SERVER_ADDRESS + url);
        HttpURLConnection con = (HttpURLConnection) obj.openConnection();
        con.setRequestMethod("PUT");
        String encoding = Base64.getEncoder().encodeToString(("username:password").getBytes(StandardCharsets.UTF_8));
        con.setRequestProperty("AUTHORIZATION", "Basic " + encoding);
        con.setRequestProperty("Content-Type", "application/json");
        con.setDoOutput(true);
        try (OutputStream output = con.getOutputStream()) {
            output.write(message.getBytes(StandardCharsets.UTF_8));
        }
        int responseCode = con.getResponseCode();

        if (responseCode == HttpURLConnection.HTTP_OK) { //success
            StringBuilder response = new StringBuilder();
            try (BufferedReader in = new BufferedReader(new InputStreamReader(con.getInputStream()))) {
                String inputLine;
                while ((inputLine = in.readLine()) != null)
                    response.append(inputLine);
            }
            System.out.println(response.toString());
            return response.toString();
        } else {
            System.out.println("PUT request failed: " + responseCode);
            return "";
        }
    }

    private String sendPostRequest(String url, String filename) throws Exception {
        MultipartUtility multipart = new MultipartUtility(SERVER_ADDRESS + url, "UTF-8");
        multipart.addFormField("description", "Media");
        multipart.addFormField("keywords", "Java,upload");
        multipart.addFilePart("file", new File(filename));
        //multipart.addFilePart("fileUpload", uploadFile2);
        List<String> response = multipart.finish();
        for (String line : response) {
            System.out.println(line);
        }
        return response.get(0);
    }
}
