package in.ayeshaayurvedic.clinic;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.time.ZonedDateTime;
import java.time.ZoneId;

@Service
public class WhatsAppAutomationService {
    private static final ZoneId CLINIC_ZONE = ZoneId.of("Asia/Kolkata");
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("EEEE, d MMMM yyyy");
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("h:mm a");

    @Value("${clinic.contact.primary:+918465058469}")
    private String primaryPhone;

    @Value("${whatsapp.api.enabled:false}")
    private boolean apiEnabled;

    public record NotificationPayload(
        String patientMessage,
        String clinicAlertMessage,
        String patientWhatsAppUrl,
        String clinicWhatsAppUrl,
        String deliveryStatus
    ) {}

    public NotificationPayload generateAndDispatch(
        Appointment appointment,
        Patient patient,
        ZonedDateTime appointmentZdt
    ) {
        String dateStr = appointmentZdt.format(DATE_FMT);
        String timeStr = appointmentZdt.format(TIME_FMT);
        boolean isVideo = "VIDEO_CALL".equalsIgnoreCase(appointment.consultationType);

        StringBuilder sb = new StringBuilder();
        sb.append("🌿 *AYESHA AYURVEDIC CLINIC*\n");
        sb.append("_Dr. Shaik Ayesha, B.A.M.S. (Andhra Board Regn: 2545/A/2025)_\n");
        sb.append("Thollabazar, Near Congress Office, Tiruvuru\n\n");
        sb.append("Namaste *").append(patient.fullName).append("*,\n");
        sb.append("Your online Ayurvedic consultation has been *booked successfully*!\n\n");
        sb.append("📅 *Date:* ").append(dateStr).append("\n");
        sb.append("⏰ *Scheduled Window:* 5:00 PM – 8:30 PM IST (Slot: ").append(timeStr).append(")\n");
        sb.append("🔖 *Booking Reference:* `").append(appointment.referenceCode).append("`\n");
        sb.append("📞 *Consultation Mode:* ").append(isVideo ? "🎥 Video Call (Zoom)" : "📞 Voice Call").append("\n\n");

        if (isVideo) {
            sb.append("*Video Consultation Details:*\n");
            sb.append("Dr. Ayesha Shaik will conduct your video consultation via Zoom.\n");
            sb.append("🔗 *Zoom Join Link:* ").append(appointment.zoomMeetingLink).append("\n");
            if (appointment.zoomPasscode != null) {
                sb.append("🔑 *Meeting Passcode:* ").append(appointment.zoomPasscode).append("\n");
            }
            sb.append("Dr. Ayesha will also verify this link with you on WhatsApp right before your slot.\n\n");
        } else {
            sb.append("*Voice Call Consultation Details:*\n");
            sb.append("Your appointment has been booked successfully! Dr. Ayesha Shaik will call you directly on your phone number during *5:00 PM – 8:30 PM IST* on that day.\n\n");
        }

        sb.append("📍 Clinic Location: Thollabazar, Jaibhavi Centre, Tiruvuru (Krishna Dist)\n");
        sb.append("📞 Clinic Helpline & WhatsApp: +91 8465058469\n");
        sb.append("🌐 Map: https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac");

        String patientMessage = sb.toString();

        // Clinic alert for Dr. Ayesha Shaik
        String clinicAlert = String.format(
            "🔔 *NEW ONLINE APPOINTMENT CONFIRMED*\nPatient: %s\nPhone: %s\nMode: %s\nDate: %s at %s\nRef: %s\nZoom: %s",
            patient.fullName,
            patient.phone,
            appointment.consultationType,
            dateStr,
            timeStr,
            appointment.referenceCode,
            isVideo ? appointment.zoomMeetingLink : "N/A (Voice Call)"
        );

        String cleanPatientPhone = patient.phone.replaceAll("[^0-9]", "");
        if (cleanPatientPhone.length() == 10) cleanPatientPhone = "91" + cleanPatientPhone;
        String cleanClinicPhone = primaryPhone.replaceAll("[^0-9]", "");

        String patientWhatsAppUrl = "https://wa.me/" + cleanPatientPhone + "?text=" + URLEncoder.encode(patientMessage, StandardCharsets.UTF_8);
        String clinicWhatsAppUrl = "https://wa.me/" + cleanClinicPhone + "?text=" + URLEncoder.encode(patientMessage, StandardCharsets.UTF_8);

        String deliveryStatus = apiEnabled ? "DISPATCHED_VIA_API" : "READY_FOR_DIRECT_SYNC";

        return new NotificationPayload(patientMessage, clinicAlert, patientWhatsAppUrl, clinicWhatsAppUrl, deliveryStatus);
    }
}
