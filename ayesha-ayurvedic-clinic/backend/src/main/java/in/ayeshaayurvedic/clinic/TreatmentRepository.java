package in.ayeshaayurvedic.clinic;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TreatmentRepository extends JpaRepository<Treatment, Long> {
    List<Treatment> findByActiveTrueOrderByIsSpecialServiceDescCategoryAsc();
}
