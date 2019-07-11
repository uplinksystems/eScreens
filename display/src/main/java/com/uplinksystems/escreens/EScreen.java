package com.uplinksystems.escreens;

import com.sun.jna.NativeLibrary;
import org.joda.time.LocalDateTime;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import uk.co.caprica.vlcj.player.MediaPlayerFactory;
import uk.co.caprica.vlcj.player.embedded.EmbeddedMediaPlayer;
import uk.co.caprica.vlcj.player.list.MediaListPlayer;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.image.BufferedImage;
import java.io.*;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class EScreen {

    private final Font largeFont, mediumFont;
    private final List<Event> events;
    private final List<Default> defaults;
    private final Map<String, Image> loadedImages;
    private final DateTimeFormatter dateTimeFormatter, dateFormatter, timeFormatter;
    private final Image missingConfigImage, missingFallbackImage, notConnectedIcon;
    private final boolean isProduction;
    private final ConnectionChecker connectionChecker;
    private final Rectangle screenSize;
    private final DisplayAccessor accessor;

    private JSONObject json;
    private String name;
    private int rotation, version;
    private Media fallback, currentMedia;
    private String hash;
    private EmbeddedMediaPlayer mediaPlayer;
    private MediaPlayerFactory mediaPlayerFactory;
    private MediaListPlayer mediaListPlayer;
    private Panel currentPanel;
    private JFrame frame;

    final static String MEDIA_DIRECTORY = "media/";
    private final String CONFIG_FILE = "config.json";
    private final String SERVER_IP = "192.168.1.129"; //"10.0.128.200";
    private final int SERVER_PORT = 5000;
    private final String SERVER_ADDRESS = "http://" + SERVER_IP + ":" + SERVER_PORT + "/";
    private final int CONFIG_UPDATE_INTERVAL = 10000;// 300000; // Every 5 minutes

    private EScreen() {
        NativeLibrary.addSearchPath("libvlc", "C:\\Program Files\\VideoLAN\\VLC");

        isProduction = "jar".equals(getClass().getResource("").getProtocol());
        try {
            hash = isProduction ? Utilities.getMD5() : "";
        } catch (IOException | URISyntaxException e) {
            hash = "";
            e.printStackTrace();
        }
        System.out.println("Hash is: " + hash);

        largeFont = new Font("serif", Font.PLAIN, 128);
        mediumFont = new Font("serif", Font.PLAIN, 90);

        events = new ArrayList<>();
        defaults = new ArrayList<>();
        loadedImages = new HashMap<>();

        screenSize = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration().getBounds();

        missingConfigImage = Utilities.TryLoadImageElseColor("/missing_config.png", screenSize, new Color(0, 255, 255));
        missingFallbackImage = Utilities.TryLoadImageElseColor("/missing_fallback.png", screenSize, new Color(255, 0, 255));
        notConnectedIcon = Utilities.TryLoadImageElseColor("/not_connected_icon.png", screenSize, new Color(36, 255, 23));

        dateTimeFormatter = DateTimeFormat.forPattern("MM/dd/yyyy HH:mm");
        dateFormatter = DateTimeFormat.forPattern("MM/dd/yyyy");
        timeFormatter = DateTimeFormat.forPattern("HH:mm");

        // Get jar version
        String stringVersion = Display.class.getPackage().getSpecificationVersion();
        version = stringVersion == null ? 0 : Integer.valueOf(stringVersion);
        System.out.println("Version is: " + version);

        connectionChecker = new ConnectionChecker(1000);
        connectionChecker.registerAddress(SERVER_IP);
        accessor = new DisplayAccessor(connectionChecker, this::getImage, rotation, screenSize, mediaPlayer, mediaPlayerFactory, mediaListPlayer);
        setupConfiguration();
        setupMediaSwitcher();
        setupDisplay();
    }

    private void setupDisplay() {
        // Todo: Find better way of waiting for display
        while (GraphicsEnvironment.isHeadless());
        try {
            Thread.sleep(4000);
        } catch (InterruptedException e ){
            e.printStackTrace();
            Thread.currentThread().interrupt();
        }

        frame = new JFrame();
        frame.getContentPane().setLayout(new CardLayout());

        // Hide cursor
        BufferedImage cursorImg = new BufferedImage(16, 16, BufferedImage.TYPE_INT_ARGB);
        Cursor blankCursor = Toolkit.getDefaultToolkit().createCustomCursor(cursorImg, new Point(0, 0), "blank cursor");
        frame.getContentPane().setCursor(blankCursor);

        // Setup VLCJ
        ArrayList<String> args = new ArrayList<>();
        if (rotation == 90 || rotation == 180) {
            args.add("--video-filter=rotate");
            args.add("--rotate-angle=180");
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
                drawMainPanel((Graphics2D) g);
            }
        };
        frame.add(Panel.MAIN.name(), mainPane);
        frame.add(Panel.MEDIA.name(), mediaPane);
        frame.setTitle("EScreen");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setExtendedState(JFrame.MAXIMIZED_BOTH);
        frame.setUndecorated(true);
        frame.addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                mediaPlayer.stop();
                mediaPlayerFactory.release();
                mediaPlayer.release();
                mediaListPlayer.release();
                System.exit(0);
            }
        });
        frame.getGraphicsConfiguration().getDevice().setFullScreenWindow(frame);
        frame.setPreferredSize(screenSize.getSize());
        switchPanel(Panel.MAIN);
        frame.pack();
        frame.setVisible(true);
        Utilities.startThreadedLoop(() -> SwingUtilities.invokeLater(frame::repaint), 100);
    }

    private void setupMediaSwitcher() {
        Utilities.startThreadedLoop(() -> {
            if (currentMedia == null)
                switchPanel(Panel.MAIN);
            else
                switchPanel(currentMedia.update(accessor));

            Media newCurrent;
            if (currentMedia != (newCurrent = getCurrentMedia())) {
                if (currentMedia != null)
                    currentMedia.stop(accessor);
                currentMedia = newCurrent;
                if (currentMedia != null)
                    currentMedia.start(accessor);
            }
        }, 100);
    }

    private Media getCurrentMedia() {
        for (Event event : events) {
            if (event.active())
                return event;
        }
        if (defaults.size() == 0)
            return fallback.isAvailable(accessor) ? fallback : null;
        Default earliest = defaults.get(0);
        for (Default def : defaults) {
            if (def.startDateTime.compareTo(LocalDateTime.now()) < 0 && def.startDateTime.compareTo(earliest.startDateTime) > 0)
                earliest = def;
        }
        if (earliest.isAvailable(accessor))
            return earliest;
        return fallback.isAvailable(accessor) ? fallback : null;
    }

    private void drawMainPanel(Graphics2D g) {
        if (json == null) {
            g.drawImage(missingConfigImage, 0, 0, screenSize.width, screenSize.height, null);
        } else if (currentMedia == null) {
            g.drawImage(missingFallbackImage, 0, 0, screenSize.width, screenSize.height, null);
        } else {
            currentMedia.draw(g, accessor);
        }
    }

    private void switchPanel(Panel panel) {
        if (currentPanel == panel)
            return;
        ((CardLayout) frame.getContentPane().getLayout()).show(frame.getContentPane(), panel.name());
        currentPanel = panel;
    }

    private void setupConfiguration() {
        if (!new File(CONFIG_FILE).exists()) {
            System.out.println("Config File is missing!");
            return;
        }
        JSONParser parser = new JSONParser();
        try {
            json = (JSONObject) parser.parse(new FileReader(CONFIG_FILE));
            parseJSON();
        } catch (Exception e) {
            System.out.println("Failed to parse config file, game over.");
            e.printStackTrace();
            json = null;
            return;
        }
        Utilities.startThreadedLoop(() -> {
            if (isProduction) {
                System.out.println("Updating JAR and media");
                System.out.println(Utilities.rsync("/home/pi/escreens/media", "/home/pi/escreens", SERVER_IP));
                System.out.println(Utilities.rsync("/home/pi/escreens/escreen.jar", "/home/pi/escreens", SERVER_IP));
                try {
                    if (!hash.equals(Utilities.getMD5())) {
                        System.out.println("New hash is: " + Utilities.getMD5());
                        System.out.println("Restarting....");
                        System.exit(0);
                    }
                } catch (IOException | URISyntaxException e) {
                    e.printStackTrace();
                }
            }
            String response = "";
            int attempts = 0;
            try {
                while (attempts < 4 && "".equals(response)) {
                    try {
                        response = Utilities.sendGetRequest(SERVER_ADDRESS + "screen/" + name + "?version=" + version);
                        if (!"".equals(response))
                            break;
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    System.out.println("Attempt " + attempts + " to pull JSON file");
                    attempts++;
                    Thread.sleep(1000);
                }
            } catch (InterruptedException e) {
                e.printStackTrace();
                return;
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
                        } catch (IOException e) {
                            System.out.println("Failed to update JSON file");
                            e.printStackTrace();
                        }
                    } else {
                        System.out.println("JSON file was up to date");
                    }
                } catch (ParseException e) {
                    System.out.println("Couldn't parse received JSON file: " + response);
                    e.printStackTrace();
                }
            }
        }, CONFIG_UPDATE_INTERVAL);
    }

    private void parseJSON() {
        // Per display config
        JSONObject config = (JSONObject) json.get("config");
        name = (String) config.get("name");
        rotation = (int) (long) config.get("rotation");

        // In case of missing files or mid download
        this.fallback = new Media((JSONObject) json.get("fallback"));

        // Default mode and file when no events are active
        JSONArray defaultArray = (JSONArray) json.get("defaults");
        for (Object object : defaultArray)
            defaults.add(new Default((JSONObject) object, dateTimeFormatter));

        // Temporary changes from defaults when all conditions are met
        JSONArray eventArray = (JSONArray) json.get("events");
        for (Object object : eventArray)
            events.add(new Event((JSONObject) object, dateTimeFormatter, timeFormatter));

        // Add any IPs to ping
        for (Default def : defaults)
            extractAddresses(def);
        for (Event event : events)
            extractAddresses(event);
        extractAddresses(fallback);
    }

    private void extractAddresses(Media media) {
        if (media.type == MediaType.MANUAL)
            for (Media manual : media.manualList)
                extractAddresses(manual);
        if ((media.type == MediaType.INSTAGRAM || media.type == MediaType.TWITCH || media.type == MediaType.YELP || media.type == MediaType.TWITTER))
            connectionChecker.registerAddress(media.info);
    }

    private Image getImage(String name) {
        String fileName = Utilities.insertImageOrientation(name, rotation);
        if (!loadedImages.containsKey(name)) {
            double angle = (rotation == 180 || rotation == 270) ? 180 : 0;
            try {
                loadedImages.put(name, Utilities.rotateImage(ImageIO.read(new File(MEDIA_DIRECTORY + fileName)), angle));
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return loadedImages.get(name);
    }

    public static void main(String[] args) {
        new EScreen();
    }
}
