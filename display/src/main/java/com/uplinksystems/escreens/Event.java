package com.uplinksystems.escreens;

import org.joda.time.DateTime;
import org.joda.time.Days;
import org.joda.time.LocalDateTime;
import org.joda.time.LocalTime;
import org.joda.time.format.DateTimeFormatter;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.time.DayOfWeek;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

class Event extends Default {
    final LocalDateTime endDateTime;
    final LocalTime startTime, endTime;
    final List<String> days;
    final long priority;

    Event(JSONObject object, DateTimeFormatter dateTimeFormatter, DateTimeFormatter timeFormatter) {
        super(object, dateTimeFormatter);
        endDateTime = dateTimeFormatter.parseLocalDateTime((String) object.get("end_date_time"));
        startTime = timeFormatter.parseLocalTime((String) object.get("start_time"));
        endTime = timeFormatter.parseLocalTime((String) object.get("end_time"));
        List<String> dayList = new ArrayList<>();
        for (Object day : (JSONArray) object.get("days"))
            dayList.add((String) day);
        days = Collections.unmodifiableList(dayList);
        priority = (long) object.get("priority");
    }

    boolean active() {
        // Todo: Finish
        boolean activeDay = false;
        for (String day: days) {
            if (day.toLowerCase().equals(LocalDateTime.now().dayOfWeek().getAsText().toLowerCase()))
                activeDay = true;
        }
        return false;
    }

    @Override
    public String toString() {
        return "Event(type=" + type.name() + ", media=" + info + ", startDate=" + startDateTime + ", endDate=" + endDateTime + ", startTime=" + startTime + ", endTime=" + endTime + ", days=" + days + ", priority=" + priority + ")";
    }
}