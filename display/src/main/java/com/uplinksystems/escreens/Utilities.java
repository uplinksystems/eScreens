package com.uplinksystems.escreens;

import org.joda.time.LocalTime;
import org.joda.time.TimeOfDay;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.sql.Time;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.TimeUnit;

final class Utilities {

    // Gets the MD5 hash of the JAR
    static String getMD5() throws IOException, URISyntaxException {
        String md5;
        try (InputStream is = Files.newInputStream(new File(Display.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toPath())) {
            md5 = org.apache.commons.codec.digest.DigestUtils.md5Hex(is);
            return md5;
        }
    }

    static String insertImageOrientation(String imageName, double rotation) {
        String[] nameParts = imageName.split("\\.");
        return nameParts[0] + ((rotation / 90 % 2 == 0) ? "_horizontal." : "_vertical.") + nameParts[1];
    }

    static Image TryLoadImageElseColor(String file, Rectangle size, Color color) {
        try {
            return ImageIO.read(Utilities.class.getResource(file));
        } catch (IOException e) {
            BufferedImage image = new BufferedImage(size.width, size.height, 1);
            Graphics2D graphics = image.createGraphics();
            graphics.setPaint(color);
            graphics.fillRect(0, 0, image.getWidth(), (image).getHeight());
            e.printStackTrace();
            return image;
        }
    }

    static BufferedImage rotateImage(Image image, double angle) {
        double angleRad = Math.toRadians(angle);
        double sin = Math.abs(Math.sin(angleRad)), cos = Math.abs(Math.cos(angleRad));
        int w = image.getWidth(null), h = image.getHeight(null);
        int neww = (int) Math.floor(w * cos + h * sin), newh = (int) Math.floor(h * cos + w * sin);
        GraphicsConfiguration gc = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration();
        BufferedImage result = gc.createCompatibleImage(neww, newh, Transparency.TRANSLUCENT);
        Graphics2D g = result.createGraphics();
        g.translate((neww - w) / 2, (newh - h) / 2);
        g.rotate(angleRad, w / 2.0, h / 2.0);
        g.drawImage(image, 0, 0, null);
        g.dispose();
        return result;
    }

    static boolean ping(String ipAddress) {
        try {
            InetAddress geek = InetAddress.getByName(ipAddress);
            return geek.isReachable(5000);
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }

    static void startThreadedLoop(Runnable runnable, long duration) {
        new Thread(() -> {
            try {
                while (true) {
                    runnable.run();
                    Thread.sleep(duration);
                }
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }).start();
    }

    static String rsync(String src, String dest, String address) {
        ProcessBuilder processBuilder = new ProcessBuilder(Arrays.asList("rsync", "-e", "ssh -o StrictHostKeyChecking=no", "-avzh", "pi@" + address + ":" + src, dest));
        processBuilder.redirectErrorStream(true);
        processBuilder.redirectOutput(ProcessBuilder.Redirect.INHERIT);
        try {
            Process process = processBuilder.start();
            process.waitFor(2, TimeUnit.MINUTES);
            BufferedReader reader =
                    new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder stringBuilder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                stringBuilder.append(line);
                stringBuilder.append(System.getProperty("line.separator"));
            }
            return stringBuilder.toString();
        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
            return e.toString();
        }
    }

    static String sendGetRequest(String address) throws IOException {
        URL obj = new URL(address);
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

    static String sendPutRequest(String address, String message) throws IOException {
        URL obj = new URL(address);
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

    static String sendPostRequest(String address, String filename) throws IOException {
        MultipartUtility multipart = new MultipartUtility(address, "UTF-8");
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
