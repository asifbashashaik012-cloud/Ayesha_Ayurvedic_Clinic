package in.ayeshaayurvedic.clinic;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface AppointmentRepository extends JpaRepository<Appointment, Long> {
    @Query("SELECT COUNT(a) FROM Appointment a WHERE a.clinicWeekStart = :week AND a.mode = 'ONLINE' AND a.status = 'CONFIRMED'")
    long countOnlineWeek(@Param("week") LocalDate week);

    @Query("SELECT COUNT(a) FROM Appointment a WHERE a.startsAt >= :from AND a.startsAt < :to AND a.mode = 'ONLINE' AND a.status = 'CONFIRMED'")
    long countOnlineDay(@Param("from") Instant from, @Param("to") Instant to);

    Optional<Appointment> findByReferenceCode(String referenceCode);

    @Query("SELECT a FROM Appointment a JOIN Patient p ON a.patientId = p.id WHERE a.referenceCode = :code AND p.phone = :phone")
    Optional<Appointment> findByReferenceCodeAndPhone(@Param("code") String code, @Param("phone") String phone);

    List<Appointment> findByClinicWeekStartOrderByStartsAtAsc(LocalDate week);

    List<Appointment> findAllByOrderByStartsAtDesc();
}
