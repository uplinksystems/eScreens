package com.uplinksystems.escreens;

enum MediaType {

    IMAGE,
    PRESENTATION,
    INSTAGRAM,
    MANUAL,
    TWITCH,
    YELP,
    VIDEO,
    TWITTER,
    SLIDESHOW,
    COUNTDOWN;

    static MediaType fromString(String string) {
        return MediaType.valueOf(string.toUpperCase());
    }
}
