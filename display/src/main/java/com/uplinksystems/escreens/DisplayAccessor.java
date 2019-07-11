package com.uplinksystems.escreens;

import uk.co.caprica.vlcj.player.MediaPlayerFactory;
import uk.co.caprica.vlcj.player.embedded.EmbeddedMediaPlayer;
import uk.co.caprica.vlcj.player.list.MediaListPlayer;

import java.awt.*;
import java.util.function.Function;

class DisplayAccessor {

    ConnectionChecker connections;
    int rotation;
    Rectangle screenSize;
    EmbeddedMediaPlayer mediaPlayer;
    MediaPlayerFactory mediaPlayerFactory;
    MediaListPlayer mediaListPlayer;
    Function<String, Image> imageProvider;

    DisplayAccessor(ConnectionChecker connections, Function<String, Image> imageProvider, int rotation, Rectangle screenSize, EmbeddedMediaPlayer mediaPlayer, MediaPlayerFactory mediaPlayerFactory, MediaListPlayer mediaListPlayer) {
        this.connections = connections;
        this.imageProvider = imageProvider;
        this.rotation = rotation;
        this.screenSize = screenSize;
        this.mediaPlayer = mediaPlayer;
        this.mediaPlayerFactory = mediaPlayerFactory;
        this.mediaListPlayer = mediaListPlayer;
    }
}
