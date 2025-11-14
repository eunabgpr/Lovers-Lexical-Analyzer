import './Header.css';
import loversLogo from "../assets/Lovers Logo Transparent.png";

type Props = {
  label: string;          // e.g. "index.love" or "Terminal"
  right?: React.ReactNode; // optional right-side content
};

export default function Header({ right }: Props) {
  return (
    <div className="main-header">
      <div className="tab">
        {/* image logo from assets (transparent) */}
        <img src={loversLogo} className="tab-icon" alt="Lovers logo" />
      </div>
      {right}
    </div>
  );
}