package com.uplinksystems.escreens;

import org.joda.time.LocalDateTime;
import org.joda.time.format.DateTimeFormatter;
import org.json.simple.JSONObject;

class Default extends Media {
    final LocalDateTime startDateTime;

    Default(JSONObject object, DateTimeFormatter dateTimeFormatter) {
        super(object);
        startDateTime = dateTimeFormatter.parseLocalDateTime((String) object.get("start_date_time"));
    }

    @Override
    public String toString() {
        return "Default(type=" + type.name() + ", media=" + info + ", startDate=" + startDateTime + ")";
    }
}