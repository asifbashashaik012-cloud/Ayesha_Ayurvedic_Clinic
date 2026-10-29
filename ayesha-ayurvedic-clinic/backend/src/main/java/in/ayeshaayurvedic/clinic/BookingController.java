package in.ayeshaayurvedic.clinic;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.time.*;
import java.util.*;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class BookingController {
    private final BookingService bookingService;
    private final AppointmentRepository appointmentRepo;
    private final PatientRepository patientRepo;
    private final TreatmentRepository treatmentRepo;

    public BookingController(
        BookingService bookingService,
        AppointmentRepository appointmentRepo,
        PatientRepository patientRepo,
        TreatmentRepository treatmentRepo
    ) {
        this.bookingService = bookingService;
        this.appointmentRepo = appointmentRepo;
        this.patientRepo = patientRepo;
        this.treatmentRepo = treatmentRepo;
    }

    public record BookingRequest(
        @NotBlank @Size(max = 120) String patientName,
        @NotBlank @Pattern(regexp = "^[+0-9][0-9 +()-]{7,19}$") String phone,
        @NotNull OffsetDateTime startsAt,
        String consultationType, // VOICE_CALL or VIDEO_CALL
        Integer age,
        String healthConcern
    ) {}

    public record CancelRequest(
        @NotBlank String referenceCode,
        @NotBlank String phone
    ) {}

    @GetMapping("/clinic")
    public Map<String, Object> clinic() {
        return Map.of(
            "name", "Ayesha Ayurvedic Clinic",
            "nameTelugu", "ఆయేషా ఆయుర్వేదిక్ క్లినిక్",
            "doctor", "Dr. Shaik Ayesha (Dr. Ayesha Shaik)",
            "qualification", "B.A.M.S., Ayurvedic Physician (Dr. N.T.R.U.H.S.)",
            "registrationNumber", "2545/A/2025",
            "stateBoard", "Andhra Board for Ayurveda (Vijayawada)",
            "primaryPhone", "+91 8465058469",
            "primaryWhatsApp", "+91 8465058469",
            "secondaryPhone", "+91 9848339262",
            "address", "10-188, Tholla Bazar, Near Congress Office / Jaibhavi Centre, Tiruvuru, Krishna District, AP - 521235",
            "googleMapsUrl", "https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac",
            "onlineTimings", "Wednesdays & Fridays, 5:00 PM – 8:30 PM IST (Max 3/day, 6/week)",
            "sundayOfflineTimings", "Sundays only: Morning 9:00 AM – 12:00 PM, Evening 4:00 PM – 8:00 PM"
        );
    }

    @GetMapping("/treatments")
    public List<Treatment> treatments() {
        return treatmentRepo.findByActiveTrueOrderByIsSpecialServiceDescCategoryAsc();
    }

    @GetMapping("/availability")
    public Map<String, Object> availability(
        @RequestParam(required = false) LocalDate from,
        @RequestParam(defaultValue = "8") int weeks
    ) {
        LocalDate startDate = (from != null) ? from : LocalDate.now(BookingService.ZONE);
        if (weeks < 1 || weeks > 12) throw new IllegalArgumentException("weeks must be between 1 and 12");
        return bookingService.availability(startDate, weeks);
    }

    @PostMapping("/appointments")
    public ResponseEntity<BookingService.BookingResponse> book(@Valid @RequestBody BookingRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED).body(bookingService.book(req));
    }

    @GetMapping("/appointments/lookup")
    public ResponseEntity<?> lookup(
        @RequestParam String referenceCode,
        @RequestParam String phone
    ) {
        var opt = appointmentRepo.findByReferenceCodeAndPhone(referenceCode.trim(), phone.trim());
        if (opt.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "No appointment found matching this reference code and phone number."));
        }
        var appt = opt.get();
        var patient = patientRepo.findById(appt.patientId).orElse(null);

        return ResponseEntity.ok(Map.of(
            "referenceCode", appt.referenceCode,
            "patientName", patient != null ? patient.fullName : "",
            "phone", patient != null ? patient.phone : "",
            "mode", appt.mode,
            "consultationType", appt.consultationType,
            "status", appt.status,
            "startsAt", appt.startsAt.atZone(BookingService.ZONE).toString(),
            "zoomMeetingLink", appt.zoomMeetingLink != null ? appt.zoomMeetingLink : "",
            "zoomPasscode", appt.zoomPasscode != null ? appt.zoomPasscode : ""
        ));
    }

    @PostMapping("/appointments/cancel")
    public ResponseEntity<?> cancel(@Valid @RequestBody CancelRequest req) {
        boolean ok = bookingService.cancel(req.referenceCode().trim(), req.phone().trim());
        if (!ok) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "Appointment could not be found or verified."));
        }
        return ResponseEntity.ok(Map.of("message", "Appointment has been cancelled successfully. Capacity has been released."));
    }
}
