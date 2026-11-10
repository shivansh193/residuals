from __future__ import annotations

from functools import cached_property
from types import TracebackType
from uuid import UUID, uuid4

from typing_extensions import Self

from .base_client import DEFAULT_TIMEOUT, BaseResidualsApiClient
from .core import (
    OPERATING_SYSTEM,
    PYTHON_RUNTIME,
    ApiResult,
    BaseRawResponse,
    HttpClient,
    Httpx2Client,
    LoggingOptionsOrDict,
    RawClient,
    RequestOptionsOrDict,
    RetryOptionsOrDict,
    json_body,
    json_decoder,
    param,
    unwrap,
)
from .errors.get_policy_error import GetPolicyErrorBody, get_policy_error_mapper
from .errors.scan_error import ScanErrorBody, scan_error_mapper
from .models.policy_out import PolicyOut
from .models.scan_req import ScanReq, ScanReqDict
from .models.scan_result import ScanResult
from .server.server import Server


class ResidualsApiClient(BaseResidualsApiClient[RawClient]):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        retry_options: int | RetryOptionsOrDict | None = None,
        logging_options: LoggingOptionsOrDict | None = None,
        custom_http_client: HttpClient | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url, timeout=timeout, retry_options=retry_options, logging_options=logging_options
        )
        self._raw_client = RawClient(
            http_client=custom_http_client if custom_http_client is not None else Httpx2Client(timeout=timeout),
            retry_options=self._retry_options,
            logging_options=self._logging_options,
            global_headers=[
                param[str]("User-Agent", "ResidualsApiClient/0.1.0 Python"),
                param[str]("X-APIMatic-Lang", "Python"),
                param[str]("X-APIMatic-Package-Version", "0.1.0"),
                param[str]("X-APIMatic-Gen-Version", "4.0.0"),
                param[str]("X-APIMatic-OS", OPERATING_SYSTEM),
                param[str]("X-APIMatic-Runtime", PYTHON_RUNTIME),
            ],
        )

    @cached_property
    def with_raw_response(self) -> ApiWithRawResponse:
        return ApiWithRawResponse(self._raw_client, self._server)

    def get_policy(self, voice_id: str, *, request_options: RequestOptionsOrDict | None = None) -> PolicyOut:
        """Send a ``GET`` request.

        Args:
            voice_id: Value sent with the request.
            request_options: Per-call overrides for this one request, such as a timeout, extra headers, or its retry
                count and statuses.

        Returns:
            Successful Response

        Raises:
            ApiError: Validation Error ``error`` is ``HttpValidationError | RawError``."""
        return unwrap(self.with_raw_response.get_policy(voice_id, request_options=request_options))

    def scan(self, body: ScanReq | ScanReqDict, *, request_options: RequestOptionsOrDict | None = None) -> ScanResult:
        """Send a ``POST`` request.

        Args:
            body: The request body.
            request_options: Per-call overrides for this one request, such as a timeout, extra headers, or its retry
                count and statuses.

        Returns:
            Successful Response

        Raises:
            ApiError: Validation Error ``error`` is ``HttpValidationError | RawError``."""
        return unwrap(self.with_raw_response.scan(body, request_options=request_options))

    def close(self) -> None:
        self._raw_client.http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        self.close()


class ApiWithRawResponse(BaseRawResponse[RawClient, Server]):
    def get_policy(
        self, voice_id: str, *, request_options: RequestOptionsOrDict | None = None
    ) -> ApiResult[PolicyOut, GetPolicyErrorBody]:
        """Send a ``GET`` request.

        Args:
            voice_id: Value sent with the request.
            request_options: Per-call overrides for this one request, such as a timeout, extra headers, or its retry
                count and statuses.

        Returns:
            An ``ApiResult`` holding the deserialized response or the error body."""
        return self._client.execute(
            http_method="GET",
            url_template=self._server.default("/policy/{voice_id}"),
            path_params=[param[str]("voice_id", voice_id)],
            decoder=json_decoder[PolicyOut],
            error_mapper=get_policy_error_mapper,
            request_options=request_options,
        )

    def scan(
        self, body: ScanReq | ScanReqDict, *, request_options: RequestOptionsOrDict | None = None
    ) -> ApiResult[ScanResult, ScanErrorBody]:
        """Send a ``POST`` request.

        Args:
            body: The request body.
            request_options: Per-call overrides for this one request, such as a timeout, extra headers, or its retry
                count and statuses.

        Returns:
            An ``ApiResult`` holding the deserialized response or the error body."""
        return self._client.execute(
            http_method="POST",
            url_template=self._server.default("/scan"),
            headers=[param[UUID]("Idempotency-Key", uuid4())],
            body=json_body[ScanReq | ScanReqDict](body),
            decoder=json_decoder[ScanResult],
            error_mapper=scan_error_mapper,
            request_options=request_options,
        )


Client = ResidualsApiClient
