package com.uplinksystems.escreens;

import java.security.InvalidParameterException;
import java.util.ArrayList;
import java.util.HashMap;

class ConnectionChecker {

    private HashMap<String, Boolean> availabilities = new HashMap<>();
    private ArrayList<String> addresses = new ArrayList<>();

    ConnectionChecker(int pollingDelay) {
        Utilities.startThreadedLoop(() -> {
            for (String address : addresses)
                availabilities.put(address, Utilities.ping(address));
        }, pollingDelay);

    }

    void registerAddress(String address) {
        if (addresses.contains(address))
            return;
        addresses.add(address);
        availabilities.put(address, false);
    }

    boolean isAvailable(String address) {
        if (!availabilities.containsKey(address))
            throw new InvalidParameterException(String.format("'%s' was not registered as an address to be polled.", address));
        return availabilities.get(address);
    }
}
