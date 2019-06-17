package com.uplinksystems.escreens;

import com.sun.jna.NativeLibrary;
import org.joda.time.DateTime;
import org.joda.time.LocalDateTime;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import uk.co.caprica.vlcj.component.EmbeddedMediaPlayerComponent;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
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

public class Display {

    private JSONObject json;
    private String name;
    private int width, height, rotation;
    private Font largeFont;
    private List<Event> events;
    private List<Default> defaults;
    private List<String> pings;
    private Map<String, Image> loadedImages;
    private Media fallback, currentMedia;
    private Map<String, Boolean> pingStatus;
    private DateTimeFormatter dateTimeFormatter;
    private Image missingConfig;
    private boolean configured;
    private JFrame frame;
    private EmbeddedMediaPlayerComponent mediaPlayer;
    private Panel currentPanel;
    private String hash;

    private final String MEDIA_DIRECTORY = "media/";
    private final String CONFIG_FILE = "config.json";
    private final String SERVER_ADDRESS = "http://192.168.1.129:5001/";
    private final String SERVER_IP = "192.168.1.129";

    private Display() throws Exception {
        NativeLibrary.addSearchPath("libvlc", "C:\\Program Files\\VideoLAN\\VLC");
        // Todo: add linux path
        //NativeLibrary.addSearchPath("libvlc", "");
        //Runtime.getRuntime().exec("sudo export DISPLAY=:0.0");
        hash = getMD5();
        System.out.println("Hash is: " + hash);
        largeFont = new Font("serif", Font.PLAIN, 128);
        events = new ArrayList<>();
        defaults = new ArrayList<>();
        pingStatus = new HashMap<>();
        pings = new ArrayList<>();
        loadedImages = new HashMap<>();
        width = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration().getBounds().width;
        height = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration().getBounds().height;
        missingConfig = ImageIO.read(getClass().getResource("/missing_config.png"));
        dateTimeFormatter = DateTimeFormat.forPattern("MM/dd/yyyy HH:mm");
        new Thread(this::updatePings).start();
        new Thread(this::updateMedia).start();
        // Forced repaints
        new Thread(() -> {
            while (true) {
                frame.invalidate();
                frame.repaint();
                try {
                    Thread.sleep(500);
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
                if (getCurrentMedia() != currentMedia) {
                    System.out.println("Invalidating");
                    currentMedia = getCurrentMedia();
                    switchPane(currentMedia.type);
                    frame.invalidate();
                    frame.repaint();
                    //frame.validate();
                }
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }

    // Handle updating config file, media, and the program
    private void configuration() throws Exception {
        if (!new File(CONFIG_FILE).exists()) {
            System.out.println("Config File is missing!");
            return;
        }
        JSONParser parser = new JSONParser();
        json = (JSONObject) parser.parse(new FileReader(CONFIG_FILE));
        parseJSON();
        configured = true;
        frame.repaint();
        while (true) {
            System.out.println("Updating JAR and media");
            Runtime.getRuntime().exec("rsync -avzh pi@" + SERVER_IP + ":/home/pi/escreens/escreen.jar /home/pi/escreens").waitFor();
            Runtime.getRuntime().exec("rsync -avzh pi@" + SERVER_IP + ":/home/pi/escreens/media /home/pi/escreens").waitFor();
            if (!hash.equals(getMD5())) {
                System.out.println("New hash is: " + getMD5());
                System.out.println("Restarting...");
                System.exit(0);
            }
            String response = "";
            int attempts = 0;
            while (attempts < 4 && "".equals(response)) {
                System.out.println("Attempt " + attempts + " to pull JSON file");
                try {
                    response = sendGetRequest("screen/" + name);
                } catch (Exception e) {
                    System.out.println(e.getMessage());
                }
                attempts++;
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
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
            // Update every 5 minutes
            Thread.sleep(300000);
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

    // Check for IPs and images
    private void processMedia(Media media) {
        if (media.type == MediaType.MANUAL)
            for (Media manual : media.media.manualList)
                processMedia(manual);
        if ((media.type == MediaType.INSTAGRAM || media.type == MediaType.TWITCH || media.type == MediaType.YELP || media.type == MediaType.TWITTER) && !pings.contains(media.media.info))
            pings.add(media.media.info);
        if (media.type == MediaType.IMAGE && !(media.media.info.endsWith("_horizontal") || media.media.info.endsWith("_vertical")))
            media.media.info += (rotation / 90 % 2 == 0) ? "_horizontal" : "_vertical";
    }

    private List<Media> manualFromJSON(JSONArray array) {
        ArrayList<Media> manual = new ArrayList<>();
        for (Object object : array)
            manual.add(mediaFromJSON((JSONObject) object));
        return manual;
    }

    private Media mediaFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        return new Media(type, type.equals(MediaType.MANUAL) ? new MediaInfo(manualFromJSON((JSONArray) object.get("media"))) : new MediaInfo((String) object.get("media")));
    }

    private Default defaultFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        return new Default(type, type.equals(MediaType.MANUAL) ? new MediaInfo(manualFromJSON((JSONArray) object.get("media"))) : new MediaInfo((String) object.get("media")), dateTimeFormatter.parseDateTime((String) object.get("start_date_time")));
    }

    private Event eventFromJSON(JSONObject object) {
        MediaType type = MediaType.fromString((String) object.get("type"));
        List<DayOfWeek> days = new ArrayList<>();
        JSONArray dayArray = (JSONArray) object.get("days");
        for (Object day : dayArray)
            days.add(DayOfWeek.valueOf((String) day));
        return new Event(type, type.equals(MediaType.MANUAL) ? new MediaInfo(manualFromJSON((JSONArray) object.get("media"))) : new MediaInfo((String) object.get("media")), dateTimeFormatter.parseDateTime((String) object.get("start_date_time")), dateTimeFormatter.parseDateTime((String) object.get("end_date_time")), timeFromString((String) object.get("start_time")), timeFromString((String) object.get("end_time")), days, (long) object.get("priority"));
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

        mediaPlayer = new EmbeddedMediaPlayerComponent() {
            @Override
            public void paintComponents(Graphics g) {
                super.paintComponents(g);
                System.out.println("REPAINT");
            }
        };
        JPanel mainPane = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                draw(g);
            }
        };
        frame.add(Panel.MAIN.name(), mainPane);
        frame.add(Panel.MEDIA.name(), mediaPlayer);
        frame.setTitle("ZapDisplay");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setExtendedState(JFrame.MAXIMIZED_BOTH);
        frame.setUndecorated(true);
        frame.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
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
        mediaPlayer.setVisible(false);
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
        if (json == null) {
            g.setColor(Color.RED);
            g.setFont(largeFont);
            g.drawImage(missingConfig, 0, 0, width, height, null);
            g.drawString("Missing configuration file...", width / 2, 200);
            return;
        }

        Media media = currentMedia;
        if (media == null) {
            System.out.println("Even the fallback is null, abandon ship!");
            return;
        }
        if (!media.available()) {
            System.out.println("Media not available: " + media.media);
            media = fallback;
        }
        System.out.println("Drawing media: " + media);
        renderMedia(g2d, media);
    }

    void switchPane(MediaType media) {
        if (currentPanel == Panel.MEDIA) {
            mediaPlayer.getMediaPlayer().stop();
        }
        if (media == MediaType.VIDEO) {
            switchPane(Panel.MEDIA);
            mediaPlayer.getMediaPlayer().playMedia(currentMedia.media.info);
        }
        else
            switchPane(Panel.MAIN);
    }

    private void switchPane(Panel panel) {
        ((CardLayout) frame.getContentPane().getLayout()).show(frame.getContentPane(), panel.name());
        currentPanel = panel;
    }

    private void renderMedia(Graphics2D g, Media media) {
        switch (media.type) {
            case IMAGE:
                if (!loadedImages.containsKey(media.media.info))
                    try {
                        loadedImages.put(media.media.info, rotateImage(ImageIO.read(new File(MEDIA_DIRECTORY + media.media.info))));
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
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

    public static void main(String[] args) throws Exception {
        try {
            UIManager.setLookAndFeel("javax.swing.plaf.nimbus.NimbusLookAndFeel");
        } catch (Exception e) {
            e.printStackTrace();
        }

        Display display = new Display();
        SwingUtilities.invokeLater(display::createGUI);
        display.configuration();
    }

    private class MediaInfo {
        String info;
        List<Media> manualList;

        public MediaInfo(String info) {
            this.info = info;
        }

        public MediaInfo(List<Media> manualList) {
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

        private boolean available() {
            if (type == MediaType.MANUAL) {
                for (Media manual : media.manualList)
                    if (manual.available())
                        return true;
                return true;
            } else if (type == MediaType.IMAGE || type == MediaType.PRESENTATION || type == MediaType.VIDEO) {
                return new File(media.info).exists();
            } else {
                return pingStatus.get(media.info);
            }
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

    private enum Panel {
        MAIN, MEDIA
    }

    private enum MediaType {
        IMAGE, PRESENTATION, INSTAGRAM, MANUAL, TWITCH, YELP, VIDEO, TWITTER;

        private static MediaType fromString(String string) {
            return MediaType.valueOf(string.toUpperCase());
        }
    }

    private BufferedImage rotateImage(Image image) {
        double angle = Math.toRadians(rotation);
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
