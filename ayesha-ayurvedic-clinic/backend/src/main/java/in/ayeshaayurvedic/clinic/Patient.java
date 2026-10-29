package in.ayeshaayurvedic.clinic;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "patient")
public class Patient {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    @Column(name = "full_name", nullable = false, length = 120)
    public String fullName;

    @Column(nullable = false, length = 20)
    public String phone;

    @Column
    public Integer age;

    @Column(name = "health_concern")
    public String healthConcern;

    @Column(name = "created_at", nullable = false)
    public Instant createdAt = Instant.now();

    public Patient() {}

    public Patient(String fullName, String phone, Integer age, String healthConcern) {
        this.fullName = fullName;
        this.phone = phone;
        this.age = age;
        this.healthConcern = healthConcern;
        this.createdAt = Instant.now();
    }
}
