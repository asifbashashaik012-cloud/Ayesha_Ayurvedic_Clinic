package in.ayeshaayurvedic.clinic;

import jakarta.persistence.*;

@Entity
@Table(name = "treatment")
public class Treatment {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    @Column(name = "name_english", nullable = false, unique = true, length = 160)
    public String nameEnglish;

    @Column(name = "name_telugu", nullable = false, length = 160)
    public String nameTelugu;

    @Column(nullable = false, length = 80)
    public String category;

    @Column(columnDefinition = "TEXT")
    public String description;

    @Column(name = "is_special_service", nullable = false)
    public Boolean isSpecialService = false;

    @Column(nullable = false)
    public Boolean active = true;

    public Treatment() {}
}
