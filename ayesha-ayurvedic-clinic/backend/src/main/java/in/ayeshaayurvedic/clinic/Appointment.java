package in.ayeshaayurvedic.clinic;

import jakarta.persistence.*;
import java.time.*;

@Entity
@Table(name = "appointment")
public class Appointment {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    @Column(name = "reference_code", nullable = false, unique = true, length = 32)
    public String referenceCode;

    @Column(name = "patient_id", nullable = false)
    public Long patientId;

    @Column(name = "doctor_id", nullable = false)
    public Long doctorId;

    @Column(nullable = false, length = 16)
    public String mode; // ONLINE, OFFLINE

    @Column(name = "consultation_type", nullable = false, length = 20)
    public String consultationType; // VOICE_CALL, VIDEO_CALL

    @Column(nullable = false, length = 20)
    public String status; // CONFIRMED, CANCELLED, COMPLETED, RESCHEDULED

    @Column(name = "starts_at", nullable = false)
    public Instant startsAt;

    @Column(name = "clinic_week_start", nullable = false)
    public LocalDate clinicWeekStart;

    @Column(name = "zoom_meeting_link")
    public String zoomMeetingLink;

    @Column(name = "zoom_passcode", length = 40)
    public String zoomPasscode;

    @Column(name = "whatsapp_status", length = 40)
    public String whatsappStatus;

    @Column(name = "created_at", nullable = false)
    public Instant createdAt = Instant.now();

    public Appointment() {}
}
