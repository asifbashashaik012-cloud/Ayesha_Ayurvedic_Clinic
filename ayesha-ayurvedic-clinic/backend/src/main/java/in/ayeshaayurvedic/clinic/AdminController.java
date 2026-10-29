package in.ayeshaayurvedic.clinic;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDate;
import java.time.temporal.TemporalAdjusters;
import java.time.DayOfWeek;
import java.util.*;

@RestController
@RequestMapping("/api/admin")
@CrossOrigin(origins = "*")
public class AdminController {
    private final AppointmentRepository appointmentRepo;
    private final PatientRepository patientRepo;
    private final ZoomAutomationService zoomService;
    private final WhatsAppAutomationService whatsAppService;

    public AdminController(
        AppointmentRepository appointmentRepo,
        PatientRepository patientRepo,
        ZoomAutomationService zoomService,
        WhatsAppAutomationService whatsAppService
    ) {
        this.appointmentRepo = appointmentRepo;
        this.patientRepo = patientRepo;
        this.zoomService = zoomService;
        this.whatsAppService = whatsAppService;
    }

    public record LoginRequest(String username, String password) {}
    public record StatusUpdateRequest(String status) {}
    public record ZoomUpdateRequest(String zoomLink, String passcode) {}

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        // Clinical administrator authentication
        if ("ayesha_clinic".equalsIgnoreCase(req.username()) && "Ayurveda@2026".equals(req.password())) {
            return ResponseEntity.ok(Map.of(
                "token", "AAC-AUTH-" + UUID.randomUUID(),
                "role", "DOCTOR_ADMIN",
                "physician", "Dr. Shaik Ayesha, B.A.M.S."
            ));
        }
        return ResponseEntity.status(401).body(Map.of("message", "Invalid clinic credentials."));
    }

    @GetMapping("/appointments")
    public ResponseEntity<?> listAppointments(@RequestParam(required = false) String week) {
        LocalDate currentMonday = LocalDate.now(BookingService.ZONE).with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        long weekBooked = appointmentRepo.countOnlineWeek(currentMonday);

        List<Appointment> list = appointmentRepo.findAllByOrderByStartsAtDesc();
        List<Map<String, Object>> result = new ArrayList<>();

        for (Appointment a : list) {
            var patient = patientRepo.findById(a.patientId).orElse(null);
            result.add(Map.of(
                "id", a.id,
                "referenceCode", a.referenceCode,
                "patientName", patient != null ? patient.fullName : "Unknown",
                "phone", patient != null ? patient.phone : "",
                "age", patient != null && patient.age != null ? patient.age : 0,
                "healthConcern", patient != null && patient.healthConcern != null ? patient.healthConcern : "",
                "mode", a.mode,
                "consultationType", a.consultationType,
                "status", a.status,
                "startsAt", a.startsAt.atZone(BookingService.ZONE).toString(),
                "zoomMeetingLink", a.zoomMeetingLink != null ? a.zoomMeetingLink : "",
                "zoomPasscode", a.zoomPasscode != null ? a.zoomPasscode : "",
                "whatsappStatus", a.whatsappStatus != null ? a.whatsappStatus : ""
            ));
        }

        return ResponseEntity.ok(Map.of(
            "weekBooked", weekBooked,
            "weeklyLimit", BookingService.WEEKLY_ONLINE_LIMIT,
            "dailyLimit", BookingService.DAILY_ONLINE_LIMIT,
            "appointments", result
        ));
    }

    @PostMapping("/appointments/{id}/status")
    public ResponseEntity<?> updateStatus(@PathVariable Long id, @RequestBody StatusUpdateRequest req) {
        var opt = appointmentRepo.findById(id);
        if (opt.isEmpty()) return ResponseEntity.notFound().build();

        Appointment a = opt.get();
        a.status = req.status().toUpperCase();
        appointmentRepo.save(a);

        return ResponseEntity.ok(Map.of("message", "Status updated to " + a.status));
    }

    @PostMapping("/appointments/{id}/zoom")
    public ResponseEntity<?> updateZoom(@PathVariable Long id, @RequestBody ZoomUpdateRequest req) {
        var opt = appointmentRepo.findById(id);
        if (opt.isEmpty()) return ResponseEntity.notFound().build();

        Appointment a = opt.get();
        a.zoomMeetingLink = req.zoomLink();
        if (req.passcode() != null) a.zoomPasscode = req.passcode();
        appointmentRepo.save(a);

        return ResponseEntity.ok(Map.of("message", "Zoom link updated successfully", "zoomMeetingLink", a.zoomMeetingLink));
    }
}
