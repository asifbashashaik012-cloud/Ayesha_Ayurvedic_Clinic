package in.ayeshaayurvedic.clinic;

import org.springframework.stereotype.Service;
import java.security.SecureRandom;

@Service
public class ZoomAutomationService {
    private static final String BASE_ZOOM_URL = "https://us05web.zoom.us/j/";
    private final SecureRandom random = new SecureRandom();

    public record ZoomMeetingDetails(String meetingId, String joinUrl, String passcode) {}

    public ZoomMeetingDetails createMeeting(String referenceCode) {
        // Generate a structured 10-digit Zoom meeting ID: 846 (clinic prefix) + 7 digits
        long roomSuffix = 1000000L + random.nextInt(9000000);
        String meetingId = "846" + roomSuffix;

        // Generate 6-character alphanumeric uppercase passcode
        String characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        StringBuilder passcode = new StringBuilder("AAC");
        for (int i = 0; i < 3; i++) {
            passcode.append(characters.charAt(random.nextInt(characters.length())));
        }

        String joinUrl = BASE_ZOOM_URL + meetingId + "?pwd=" + passcode;

        return new ZoomMeetingDetails(meetingId, joinUrl, passcode.toString());
    }
}
