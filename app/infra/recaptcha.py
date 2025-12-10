"""reCAPTCHA Enterprise verification."""
from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment
from loguru import logger
from config import settings

RECAPTCHA_SITE_KEY = "6LeatyYsAAAAACAUey2hO0HLvyQshete6w1foH5s"


async def verify_recaptcha_enterprise(
    token: str | None,
    expected_action: str = 'signup',
    remote_ip: str | None = None,
) -> bool:
    """
    Verify reCAPTCHA Enterprise token.
    
    Args:
        token: The reCAPTCHA token from the client
        expected_action: The expected action name (default: 'signup')
        remote_ip: Optional remote IP address
        
    Returns:
        True if verification succeeds, False otherwise
    """
    project_id = getattr(settings, 'RECAPTCHA_PROJECT_ID', None)
    recaptcha_site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', None)

    if not token:
        logger.warning("reCAPTCHA token not provided")
        if not project_id or not recaptcha_site_key:
            logger.warning(
                "reCAPTCHA not configured and token missing, skipping verification",
            )
            return True
        return False

    if not project_id or not recaptcha_site_key:
        logger.warning(
            "RECAPTCHA_PROJECT_ID or RECAPTCHA_SITE_KEY not configured, skipping verification",
        )
        return True  # Allow if not configured (for development)

    try:
        client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

        event = recaptchaenterprise_v1.Event()
        event.site_key = recaptcha_site_key
        event.token = token
        if remote_ip:
            event.user_ip_address = remote_ip

        assessment = recaptchaenterprise_v1.Assessment()
        assessment.event = event

        project_name = f"projects/{project_id}"

        request = recaptchaenterprise_v1.CreateAssessmentRequest()
        request.assessment = assessment
        request.parent = project_name

        response = client.create_assessment(request)

        if not response.token_properties.valid:
            invalid_reason = response.token_properties.invalid_reason
            logger.warning(
                f"reCAPTCHA token invalid: {invalid_reason}",
            )
            return False

        if response.token_properties.action != expected_action:
            logger.warning(
                f"reCAPTCHA action mismatch. Expected: {expected_action}, "
                f"Got: {response.token_properties.action}",
            )
            return False

        score = response.risk_analysis.score
        threshold = getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.5)

        if response.risk_analysis.reasons:
            reasons = [reason.name for reason in response.risk_analysis.reasons]
            logger.info(f"reCAPTCHA risk reasons: {reasons}")

        if score >= threshold:
            logger.info(
                f"reCAPTCHA verification successful (score: {score}, threshold: {threshold})",
            )
            return True
        logger.warning(
            f"reCAPTCHA verification failed (score: {score}, threshold: {threshold})",
        )
        return False

    except Exception as e:
        logger.error(f"Error verifying reCAPTCHA Enterprise: {e}")
        return False


async def verify_recaptcha_v3(
    token: str | None,
    remote_ip: str | None = None,
    expected_action: str = 'signup',
) -> bool:
    """Alias for verify_recaptcha_enterprise for backward compatibility."""
    return await verify_recaptcha_enterprise(token, expected_action, remote_ip)
