package in.ayeshaayurvedic.clinic;

import jakarta.persistence.*;

@Entity
@Table(name = "doctor")
public class Doctor {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    @Column(name = "full_name", nullable = false, length = 120)
    public String fullName;

    @Column(nullable = false, length = 120)
    public String qualification;

    @Column(name = "registration_number", nullable = false, length = 60)
    public String registrationNumber;

    @Column(name = "state_board", nullable = false, length = 120)
    public String stateBoard;

    @Column(name = "phone_primary", nullable = false, length = 20)
    public String phonePrimary;

    @Column(name = "phone_secondary", length = 20)
    public String phoneSecondary;

    @Column(nullable = false)
    public Boolean active = true;

    public Doctor() {}
}
