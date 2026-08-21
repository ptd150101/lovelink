type ProfileInfoRowProps = {
  label: string;
  value: string;
};

export function ProfileInfoRow({ label, value }: ProfileInfoRowProps) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
