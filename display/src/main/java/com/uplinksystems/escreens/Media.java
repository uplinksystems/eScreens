package com.uplinksystems.escreens;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.awt.*;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static com.uplinksystems.escreens.EScreen.MEDIA_DIRECTORY;

class Media {

    final MediaType type;
    final String info;
    final List<Media> manualList;
    final String name;

    private ArrayList<File> files = new ArrayList<>();

    Media(JSONObject object) {
        type = MediaType.fromString((String) object.get("type"));
        name = (String) object.get("name");
        switch (type) {
            case MANUAL:
                ArrayList<Media> manual = new ArrayList<>();
                for (Object manualObject : (JSONArray) object.get("media"))
                    manual.add(new Media((JSONObject) manualObject));
                manualList = Collections.unmodifiableList(manual);
                info = null;
                break;
            default:
                info = (String) object.get("media");
                manualList = null;
        }
    }

    void start(DisplayAccessor display) {

    }

    Panel update(DisplayAccessor display) {
        if (type == MediaType.SLIDESHOW || type == MediaType.VIDEO)
            return Panel.MEDIA;
        return Panel.MAIN;
    }

    void stop(DisplayAccessor display) {

    }

    // Called from main panel
    void draw(Graphics2D g, DisplayAccessor display) {

    }

    boolean isAvailable(DisplayAccessor display) {
        switch (type) {
            case IMAGE:
                if (files.size() == 0)
                    files.add(new File(MEDIA_DIRECTORY + Utilities.insertImageOrientation(info, display.rotation)));
                return files.get(0).exists();
            case MANUAL:
                for (Media manual : manualList)
                    if (manual.isAvailable(display))
                        return true;
                return true;
            case SLIDESHOW:
                // Todo: ensure this one works
                String[] entries = info.split(", ");
                for (int i = 1; i < entries.length; i++) {
                    if (files.size() < i)
                        files.add(new File(MEDIA_DIRECTORY + entries[i]));
                    if (!files.get(i - 1).exists())
                        return false;
                }
                return true;
            case PRESENTATION:
            case VIDEO:
                if (files.size() == 0)
                    files.add(new File(MEDIA_DIRECTORY + info));
                return files.get(0).exists();
            case COUNTDOWN:
            case INSTAGRAM:
            case TWITTER:
            case TWITCH:
            case YELP:
                return display.connections.isAvailable(info);
            default:
                return false;
        }
    }

    @Override
    public String toString() {
        return "Media(type=" + type.name() + ", media=" + info + ")";
    }
}