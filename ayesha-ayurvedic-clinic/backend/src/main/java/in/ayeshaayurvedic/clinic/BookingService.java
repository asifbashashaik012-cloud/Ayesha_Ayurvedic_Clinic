package in.ayeshaayurvedic.clinic;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.*;
import java.time.temporal.TemporalAdjusters;
import java.util.*;
import java.security.SecureRandom;

@Service
public class BookingService {
    public static final ZoneId ZONE = ZoneId.of("Asia/Kolkata");
    public static final int DAILY_ONLINE_LIMIT = 3;
    public static final int WEEKLY_ONLINE_LIMIT = 6;

    private final AppointmentRepository appointments;
    private final PatientRepository patients;
    private final BookingWeekLockRepository locks;
    private final WhatsAppAutomationService whatsAppService;
    private final ZoomAutomationService zoomService;
    private final boolean bookingEnabled;

    public BookingService(
        AppointmentRepository appointments,
        PatientRepository patients,
        BookingWeekLockRepository locks,
        WhatsAppAutomationService whatsAppService,
        ZoomAutomationService zoomService,
        @Value("${clinic.booking.enabled:true}") boolean bookingEnabled
    ) {
        this.appointments = appointments;
        this.patients = patients;
        this.locks = locks;
        this.whatsAppService = whatsAppService;
        this.zoomService = zoomService;
        this.bookingEnabled = bookingEnabled;
    }

    public record BookingResponse(
        String reference,
        String mode,
        String consultationType,
        OffsetDateTime startsAt,
        String message,
        String zoomMeetingLink,
        String zoomPasscode,
        WhatsAppAutomationService.NotificationPayload notification
    ) {}

    public record DayAvailability(
        String date,
        String weekday,
        long booked,
        int dayLimit,
        long weekBooked,
        int weekLimit,
        boolean available,
        List<String> availableSlots
    ) {}

    public Map<String, Object> availability(LocalDate fromDate, int weeks) {
        LocalDate startMonday = fromDate.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        List<DayAvailability> days = new ArrayList<>();

        List<String> standardSlots = List.of("17:00", "17:45", "18:30", "19:15", "20:00");

        for (int w = 0; w < weeks; w++) {
            LocalDate weekMon = startMonday.plusWeeks(w);
            long weekCount = appointments.countOnlineWeek(weekMon);

            for (DayOfWeek d : List.of(DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY)) {
                LocalDate day = weekMon.with(TemporalAdjusters.nextOrSame(d));
                Instant dayStart = day.atStartOfDay(ZONE).toInstant();
                Instant dayEnd = day.plusDays(1).atStartOfDay(ZONE).toInstant();

                long dayCount = appointments.countOnlineDay(dayStart, dayEnd);
                boolean hasCapacity = dayCount < DAILY_ONLINE_LIMIT && weekCount < WEEKLY_ONLINE_LIMIT;

                days.add(new DayAvailability(
                    day.toString(),
                    d.toString(),
                    dayCount,
                    DAILY_ONLINE_LIMIT,
                    weekCount,
                    WEEKLY_ONLINE_LIMIT,
                    hasCapacity,
                    hasCapacity ? standardSlots : Collections.emptyList()
                ));
            }
        }

        return Map.of(
            "timezone", ZONE.getId(),
            "bookingWeekStarts", "MONDAY",
            "dailyLimit", DAILY_ONLINE_LIMIT,
            "weeklyLimit", WEEKLY_ONLINE_LIMIT,
            "days", days,
            "bookingEnabled", bookingEnabled,
            "clinicTimings", "Wednesday & Friday 5:00 PM – 8:30 PM IST",
            "primaryPhone", "+918465058469"
        );
    }

    @Transactional
    public BookingResponse book(BookingController.BookingRequest r) {
        if (!bookingEnabled) {
            throw new BookingDisabledException();
        }

        ZonedDateTime zdt = r.startsAt().atZoneSameInstant(ZONE);
        LocalDate d = zdt.toLocalDate();
        LocalTime t = zdt.toLocalTime();

        // 1. Mandatory Invariant: Day check (Wednesday or Friday only)
        if (d.getDayOfWeek() != DayOfWeek.WEDNESDAY && d.getDayOfWeek() != DayOfWeek.FRIDAY) {
            throw new IllegalArgumentException("Online consultations are available only on Wednesdays and Fridays.");
        }

        // 2. Mandatory Invariant: Window check (5:00 PM to 8:30 PM IST)
        if (t.isBefore(LocalTime.of(17, 0)) || t.isAfter(LocalTime.of(20, 30))) {
            throw new IllegalArgumentException("Consultation time must be between 5:00 PM and 8:30 PM IST.");
        }

        // 3. Concurrency Lock: Lock by Monday week row
        LocalDate weekStart = d.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        locks.ensure(weekStart);
        locks.lock(weekStart);

        // 4. Strict Limits: Day <= 3, Week <= 6
        Instant dayStart = d.atStartOfDay(ZONE).toInstant();
        Instant dayEnd = d.plusDays(1).atStartOfDay(ZONE).toInstant();

        long currentDayCount = appointments.countOnlineDay(dayStart, dayEnd);
        if (currentDayCount >= DAILY_ONLINE_LIMIT) {
            throw new CapacityConflictException("This day has reached its maximum online capacity (3 appointments). Please select another date.");
        }

        long currentWeekCount = appointments.countOnlineWeek(weekStart);
        if (currentWeekCount >= WEEKLY_ONLINE_LIMIT) {
            throw new CapacityConflictException("This clinic week has reached its maximum capacity (6 appointments). Please select a date in a following week.");
        }

        // 5. Patient Record
        Patient patient = new Patient(
            r.patientName().trim(),
            r.phone().trim(),
            r.age(),
            r.healthConcern() != null ? r.healthConcern().trim() : null
        );
        patient = patients.save(patient);

        // 6. Consultation Mode & Zoom Integration
        String consultationType = (r.consultationType() != null && "VIDEO_CALL".equalsIgnoreCase(r.consultationType()))
            ? "VIDEO_CALL" : "VOICE_CALL";

        String zoomLink = null;
        String zoomPass = null;
        if ("VIDEO_CALL".equals(consultationType)) {
            var zoomDetails = zoomService.createMeeting(reference());
            zoomLink = zoomDetails.joinUrl();
            zoomPass = zoomDetails.passcode();
        }

        // 7. Save Appointment
        Appointment appointment = new Appointment();
        appointment.referenceCode = reference();
        appointment.patientId = patient.id;
        appointment.doctorId = 1L; // Dr. Shaik Ayesha
        appointment.mode = "ONLINE";
        appointment.consultationType = consultationType;
        appointment.status = "CONFIRMED";
        appointment.startsAt = r.startsAt().toInstant();
        appointment.clinicWeekStart = weekStart;
        appointment.zoomMeetingLink = zoomLink;
        appointment.zoomPasscode = zoomPass;
        appointment.whatsappStatus = "PENDING";
        appointment = appointments.save(appointment);

        // 8. Automated WhatsApp Notification Payload
        var notification = whatsAppService.generateAndDispatch(appointment, patient, zdt);
        appointment.whatsappStatus = notification.deliveryStatus();
        appointments.save(appointment);

        String modeMessage = "VOICE_CALL".equals(consultationType)
            ? "Your appointment has been booked successfully! Dr. Ayesha Shaik will call you during 5:00 PM – 8:30 PM IST on that day."
            : "Your appointment has been booked successfully! The doctor will send you the link of the Zoom meeting on WhatsApp in automation.";

        return new BookingResponse(
            appointment.referenceCode,
            "ONLINE",
            consultationType,
            r.startsAt(),
            modeMessage,
            zoomLink,
            zoomPass,
            notification
        );
    }

    @Transactional
    public boolean cancel(String referenceCode, String phone) {
        var opt = appointments.findByReferenceCodeAndPhone(referenceCode, phone);
        if (opt.isEmpty()) return false;

        Appointment appointment = opt.get();
        if ("CANCELLED".equals(appointment.status)) return true;

        appointment.status = "CANCELLED";
        appointments.save(appointment);
        return true;
    }

    private String reference() {
        byte[] b = new byte[4];
        new SecureRandom().nextBytes(b);
        return "AAC-" + HexFormat.of().formatHex(b).toUpperCase();
    }

    public static class BookingDisabledException extends RuntimeException {
        public BookingDisabledException() { super("Online booking is temporarily offline for maintenance."); }
    }

    public static class CapacityConflictException extends RuntimeException {
        public CapacityConflictException(String msg) { super(msg); }
    }
}
